from collections import deque
from collections import defaultdict
from itertools import permutations
from itertools import groupby
from itertools import permutations
from math import ceil
import random
import string
import uuid

from markdownx.models import MarkdownxField

from datetime import timedelta
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils import timezone

from apps.item import models as item_models
from apps.study import models as study_models


class Questionnaire(models.Model):
    slug = models.SlugField(
        unique=True,
        max_length=110,
    )
    study = models.ForeignKey(
        'lrex_study.Study',
        on_delete=models.CASCADE,
        related_name='questionnaires',
    )
    number = models.IntegerField()
    item_lists = models.ManyToManyField(item_models.ItemList)

    class Meta:
        ordering = ['number']

    @staticmethod
    def compute_slug(study, number):
        return '{}-{}'.format(study.slug, number)

    def save(self, *args, **kwargs):
        self.slug = self.compute_slug()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('questionnaire', args=[self.study.slug, self.slug])

    @cached_property
    def items(self):
        return [
            questionnaire_item.item
            for questionnaire_item
            in self.questionnaire_items.all().prefetch_related('item')
        ]

    @cached_property
    def questionnaire_items_preview(self):
        queryset = self.questionnaire_items.prefetch_related(
            'item',
            'item__materials',
            'questionnaire',
        )
        queryset = queryset[:10]
        return queryset

    def _generate_block_items(self, block_items, block_offset):
        questionnaire_items = []
        for i, item in enumerate(block_items):
            questionnaire_item = QuestionnaireItem(
                number=block_offset + i,
                questionnaire=self,
                item=item,
            )
            questionnaire_items.append(questionnaire_item)
        return questionnaire_items

    def _generate_items_random(self, block_items, block_offset):
        random.shuffle(block_items)
        return self._generate_block_items(block_items, block_offset)

    PSEUDO_RANDOMIZE_TRIES = 1000

    def _materials_items_with_alternating_conditions(self, materials_items):
        n_tries = self.PSEUDO_RANDOMIZE_TRIES
        original_items = deque(materials_items)
        while n_tries:
            items = original_items.copy()
            pseudo_random_items = deque()
            random.shuffle(items)
            last_item = None
            bubble_fails = 0
            while bubble_fails <= len(items):
                try:
                    item = items.popleft()
                except IndexError:
                    break
                if not last_item or last_item.condition != item.condition:
                    pseudo_random_items.append(item)
                    bubble_fails = 0
                else:
                    items.append(item)
                    bubble_fails += 1
                last_item = item
            if len(items) == 0:
                return pseudo_random_items
            n_tries -= 1
        raise RuntimeError('Unable to compute alternating conditions.')

    def _pseudo_randomized_materials_items(self, block_items, materials_dict):
        items_by_materials = {}
        for id, materials_items in groupby(block_items, lambda x: x.materials_id):
            items = list(materials_items)
            if materials_dict[id].is_filler or materials_dict[id].condition_count == 1:
                random.shuffle(items)
            else:
                items = self._materials_items_with_alternating_conditions(items)
            items_by_materials[id] = items
        return items_by_materials

    def _generate_items_pseudo_random(self, block_items, block_offset, block_slots, materials_dict):
        questionnaire_items = []
        if len(block_slots) != len(block_items):
            raise RuntimeError('Block does not match master slots.')
        items_by_materials = self._pseudo_randomized_materials_items(block_items, materials_dict)
        for i, slot_materials in enumerate(block_slots):
            item = items_by_materials[slot_materials].pop()
            if not item:
                raise RuntimeError('Block does not match master slots.')
            questionnaire_item = QuestionnaireItem(
                number=block_offset + i,
                questionnaire=self,
                item=item,
            )
            questionnaire_items.append(questionnaire_item)
        return questionnaire_items

    PSEUDO_RANDOMIZE_SLOT_TRIES = 1000

    def _compute_block_slots(self, block_items, materials_dict):
        filler = list([ id for id, materials in materials_dict.items() if materials.is_filler])
        n_tries = self.PSEUDO_RANDOMIZE_SLOT_TRIES
        while n_tries:
            slots = []
            items = block_items.copy()
            random.shuffle(items)
            colliding = []
            last_item = None
            for item in items:
                if (
                        item.materials_id in filler
                        or not last_item
                        or last_item.materials_id in filler
                        or last_item.materials_id != item.materials_id
                ):
                    slots.append(item.materials_id)
                else:
                    colliding.append(item)
                last_item = item
            resolution_failed = False
            for item in colliding:
                slot_size = len(slots)
                n_insert_tries =  int(slot_size / 4)
                while n_insert_tries:
                    pos = random.randint(0, slot_size - 2)
                    if item.materials_id != slots[pos] and item.materials_id != slots[pos + 1]:
                        slots.insert(pos + 1, item.materials_id)
                        break
                    n_insert_tries -= 1
                if not n_insert_tries:
                    resolution_failed = True
            if not resolution_failed:
                return slots
            else:
                n_tries -= 1
        raise RuntimeError('Unable to compute slots.')

    def _items_by_block(self, materials_dict):
        items = item_models.Item.objects.filter(
            itemlist__in=self.item_lists.all()
        ).order_by(
            'materials', 'number', 'condition'
        ).all()
        items_by_block = {}
        for item in items:
            block = materials_dict[item.materials_id].auto_block
            if not block:
                block = item.block
            items_by_block.setdefault(block, [])
            items_by_block[block].append(item)
        return items_by_block

    def _compute_slots(self, materials_dict, block_randomization, items_by_block):
        slots = {}
        for block, block_items in items_by_block.items():
            block_items = list(block_items)
            if block_randomization[block] == QuestionnaireBlock.RANDOMIZATION_PSEUDO:
                slots[block] = self._compute_block_slots(block_items, materials_dict)
        return slots

    def _random_question_permutations(self, questions, n_items):
        questions = [question.number for question in questions]
        question_permutations = list(permutations(questions))
        n_permutations = len(question_permutations)
        per_permutation = ceil(n_items/n_permutations)
        question_permutations = per_permutation*question_permutations
        random.shuffle(question_permutations)
        return question_permutations

    def _randomize_question_order(self, questions, questionnaire_items):
        n_items = len(questionnaire_items)
        question_permutations = self._random_question_permutations(questions, n_items)
        for questionnaire_item, permutation in zip(questionnaire_items, question_permutations):
            questionnaire_item.question_order = ','.join(str(p) for p in permutation)

    def _random_scale_permutations(self, question, n_items):
        scale = range(0, question.scale_values.count())
        scale_permutations = list(permutations(scale))
        n_permutations = len(scale_permutations)
        per_permutation = ceil(n_items/n_permutations)
        scale_permutations = per_permutation*scale_permutations
        random.SystemRandom().shuffle(scale_permutations)
        return scale_permutations

    def _randomize_question_scales(self, questions, questionnaire_items):
        n_items = len(questionnaire_items)
        question_properties = []
        for question in questions:
            if question.randomize_scale:
                scale_permutations = self._random_scale_permutations(question, n_items)
                for questionnaire_item, permutation in zip(questionnaire_items, scale_permutations):
                    question_property = QuestionProperty(
                        number=question.number,
                        questionnaire_item=questionnaire_item,
                        scale_order=','.join(str(p) for p in permutation)
                    )
                    question_properties.append(question_property)
        QuestionProperty.objects.bulk_create(question_properties)

    def _has_pseudo_randomization(self, block_randomization):
        return any(
            randomization for randomization in block_randomization.values()
            if randomization == QuestionnaireBlock.RANDOMIZATION_PSEUDO
        )

    def generate_questionnaire_items(self, materials_list, block_randomization, randomize_scales, questions):
        questionnaire_items = []
        random.seed()
        materials_dict = {e.id: e for e in materials_list}
        items_by_block = self._items_by_block(materials_dict)
        if self._has_pseudo_randomization(block_randomization):
            slots = self._compute_slots(materials_dict, block_randomization, items_by_block)
        block_offset = 0
        for block, block_items in items_by_block.items():
            if block_randomization[block] == QuestionnaireBlock.RANDOMIZATION_TRUE:
                questionnaire_items.extend(self._generate_items_random(block_items, block_offset))
            elif block_randomization[block] == QuestionnaireBlock.RANDOMIZATION_PSEUDO:
                questionnaire_items.extend(
                    self._generate_items_pseudo_random(block_items, block_offset, slots[block], materials_dict)
                )
            else:
                questionnaire_items.extend(self._generate_block_items(block_items, block_offset))
            block_offset += len(block_items)
        if self.study.pseudo_randomize_question_order:
            self._randomize_question_order(questions, questionnaire_items)
        if randomize_scales:
            self._randomize_question_scales(questions, questionnaire_items)
        return questionnaire_items

    def __str__(self):
        return str(self.number)


class QuestionnaireBlock(models.Model):
    block = models.IntegerField()
    instructions = MarkdownxField(
        max_length=5000,
        help_text='These instructions will be presented to the participant before the questionnaire block begins.',
        blank=True,
        null=True,
    )
    short_instructions = MarkdownxField(
        max_length=3000,
        help_text='You can optionally provide a shorter version of the block instructions that the participant can '
                  'access again during participation as a reminder of the task.',
        blank=True,
        null=True,
    )
    RANDOMIZATION_PSEUDO = 'pseudo'
    RANDOMIZATION_NONE = 'none'
    RANDOMIZATION_TRUE = 'true'
    RANDOMIZATION_BASE = (
        (RANDOMIZATION_TRUE, 'Randomize'),
        (RANDOMIZATION_NONE, 'Keep item order'),
    )
    RANDOMIZATION_TYPE = (
        (RANDOMIZATION_PSEUDO, 'Pseudo-randomize'),
        *RANDOMIZATION_BASE
    )
    randomization = models.CharField(
        max_length=8,
        choices=RANDOMIZATION_TYPE,
        default=RANDOMIZATION_PSEUDO,
        help_text='Randomize items in each questionnaire block.',
    )
    study = models.ForeignKey(
        'lrex_study.Study',
        on_delete=models.CASCADE,
        related_name='questionnaire_blocks',
    )

    class Meta:
        ordering = ['block']

    def __str__(self):
        return str(self.block)


class QuestionnaireItem(models.Model):
    number = models.IntegerField()
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='questionnaire_items')
    item = models.ForeignKey(item_models.Item, on_delete=models.CASCADE)
    question_order = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['number']

    @cached_property
    def question_order_user(self):
        return ','.join(str(int(question_num) + 1) for question_num in self.question_order.split(','))

    def __str__(self):
        return '{} - {}'.format(self.number, self.item)


class QuestionProperty(models.Model):
    number = models.IntegerField()
    questionnaire_item = models.ForeignKey(
        QuestionnaireItem,
        on_delete=models.CASCADE,
        related_name='question_properties',
    )
    scale_order = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['number']

    @cached_property
    def question_scale_user(self):
        scale = []
        study = self.questionnaire_item.questionnaire.study
        question = study.questions.get(number=self.number)
        scale_labels = [scale_value.label for scale_value in question.scale_values.all()]
        for pos in self.scale_order.split(','):
            scale.append(scale_labels[int(pos)])
        return ','.join(scale)


class Trial(models.Model):
    slug = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    created = models.DateTimeField(
        default=timezone.now,
    )
    ended = models.DateTimeField(
        blank=True,
        null=True,
    )
    participant_id = models.CharField(
        max_length=200,
        help_text='Provide an identification number/name (as instructed by the experimenter).',
        verbose_name='ID',
        blank=True,
        null=True,
    )
    is_test = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ['created']

    def save(self, *args, **kwargs):
        if (
                not self.participant_id
                and self.questionnaire.study.participant_id == study_models.Study.PARTICIPANT_ID_RANDOM
        ):
            random.seed()
            self.participant_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        return super().save(*args, **kwargs)

    @cached_property
    def number(self):
        return Trial.objects.filter(
            questionnaire__study=self.questionnaire.study, is_test=False, created__lt=self.created,
        ).count() + 1

    @cached_property
    def items(self):
        return self.questionnaire.items

    @cached_property
    def ratings_completed(self):
        return Rating.objects.filter(trial=self, question=0).count()

    @cached_property
    def ratings_count(self):
        return len(self.items)

    @cached_property
    def current_block(self):
        questionnaire_item = QuestionnaireItem.objects.get(
            questionnaire=self.questionnaire,
            number=self.ratings_completed
        )
        questionnaire_block = QuestionnaireBlock.objects.get(
            study=self.questionnaire.study,
            block=questionnaire_item.item.materials_block
        )
        return questionnaire_block

    @property
    def is_finished(self):
        return self.ratings_completed == self.ratings_count

    @property
    def time_taken(self):
        if self.ended:
            return (self.ended - self.created).seconds

    ABANDONED_AFTER_HRS = 1

    @property
    def is_abandoned(self):
        if not self.is_finished:
            latest_rating = self.rating_set.exclude(created=None).order_by('created').last()
            if latest_rating:
                last_time_active = latest_rating.created
            else:
                last_time_active = self.created
            return last_time_active + timedelta(hours=self.ABANDONED_AFTER_HRS) < timezone.now()
        return False

    def init(self, study):
        self.questionnaire = study.next_questionnaire(is_test=self.is_test)
        self.save()

    def get_absolute_url(self):
        return reverse('trial', args=[self.slug])

    def __str__(self):
        return self.participant_id if self.participant_id else str(self.number)


class Rating(models.Model):
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE)
    created = models.DateTimeField(default=timezone.now, blank=True, null=True)
    questionnaire_item = models.ForeignKey(QuestionnaireItem, on_delete=models.CASCADE, related_name='ratings')
    question = models.IntegerField(default=0)
    scale_value = models.ForeignKey(study_models.ScaleValue, on_delete=models.CASCADE)
    comment = models.CharField(
        blank=True,
        null=True,
        max_length=2000,
    )

    class Meta:
        ordering = ['trial', 'questionnaire_item', 'question']
        unique_together = ['trial', 'questionnaire_item', 'question']

    @cached_property
    def question_user(self):
        return self.question + 1

    @cached_property
    def question_object(self):
        return self.questionnaire_item.questionnaire.study.questions.get(number=self.question)


class DemographicValue(models.Model):
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE, related_name='demographics')
    field = models.ForeignKey(study_models.DemographicField, on_delete=models.CASCADE)
    value = models.CharField(
        max_length=2000,
    )

    class Meta:
        ordering = ['trial', 'field']
