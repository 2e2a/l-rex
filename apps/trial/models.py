from collections import deque
from itertools import groupby
from itertools import permutations
from itertools import repeat
from math import ceil
import random
import string
import uuid

from markdownx.models import MarkdownxField

from collections import OrderedDict
from datetime import timedelta
from enum import Enum
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils import timezone

from apps.experiment import models as experiment_models
from apps.item import models as item_models
from apps.study import models as study_models


class Questionnaire(models.Model):
    slug = models.SlugField(
        unique=True,
        max_length=110,
    )
    study = models.ForeignKey(
        'lrex_study.Study',
        on_delete=models.CASCADE
    )
    number = models.IntegerField()
    item_lists = models.ManyToManyField(item_models.ItemList)

    class Meta:
        ordering = ['number']

    def save(self, *args, **kwargs):
        self.slug = '{}-{}'.format(self.study.slug, self.number)
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('questionnaire', args=[self.study.slug, self.slug])

    @cached_property
    def items(self):
        return [
            questionnaire_item.item
            for questionnaire_item
            in self.questionnaireitem_set.all().prefetch_related('item')
        ]

    @cached_property
    def questionnaire_items_preview(self):
        return self.questionnaireitem_set.all().prefetch_related('item')[:10]

    @cached_property
    def questionnaire_items(self):
        return self.questionnaireitem_set.all().prefetch_related('item')

    @cached_property
    def questionnaire_items_by_block(self):
        blocks = OrderedDict()
        for questionnaire_item in self.questionnaireitem_set.all():
            if questionnaire_item.item.experiment_block in blocks:
                blocks[questionnaire_item.item.experiment_block].append(questionnaire_item)
            else:
                blocks[questionnaire_item.item.experiment_block] = [questionnaire_item]
        return blocks

    def block_items(self, block):
        return self.questionnaire_items_by_block[block]

    def _block_randomization(self):
        block_randomization = OrderedDict()
        questionnaire_blocks = self.study.questionnaireblock_set.all()
        for questionnaire_block in questionnaire_blocks:
            block_randomization[questionnaire_block.block] = questionnaire_block.randomization
        return block_randomization

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
        random.SystemRandom().shuffle(block_items)
        return self._generate_block_items(block_items, block_offset)

    PSEUDO_RANDOMIZE_TRIES = 10000

    def _experiment_items_with_alternating_conditions(self, experiment_items):
        n_tries = self.PSEUDO_RANDOMIZE_TRIES
        original_items = deque(experiment_items)
        while n_tries:
            items = original_items.copy()
            pseudo_random_items = deque()
            random.SystemRandom().shuffle(items)
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
        raise RuntimeError('Unable to compute alternating conditions')

    def _pseudo_randomized_experiment_items(self, block_items, experiments):
        items_by_experiment = {}
        for id, experiment_items in groupby(block_items, lambda x: x.experiment_id):
            items = list(experiment_items)
            if experiments[id].is_filler or len(experiments[id].conditions) == 1:
                random.SystemRandom().shuffle(items)
            else:
                items = self._experiment_items_with_alternating_conditions(items)
            items_by_experiment[id] = items
        return items_by_experiment

    def _generate_items_pseudo_random(self, block_items, block_offset, block_slots, experiments):
        questionnaire_items = []
        if len(block_slots) != len(block_items):
            raise RuntimeError('Block does not match master slots')
        items_by_experiment = self._pseudo_randomized_experiment_items(block_items, experiments)
        for i, slot_experiment in enumerate(block_slots):
            item = items_by_experiment[slot_experiment].pop()
            if not item:
                raise RuntimeError('Block does not match master slots')
            questionnaire_item = QuestionnaireItem(
                number=block_offset + i,
                questionnaire=self,
                item=item,
            )
            questionnaire_items.append(questionnaire_item)
        return questionnaire_items

    def _compute_block_slots(self, block_items, experiments):
        filler = list([ id for id, experiment in experiments.items() if experiment.is_filler])
        n_tries = 10
        while n_tries:
            slots = []
            items = block_items.copy()
            random.SystemRandom().shuffle(items)
            colliding = []
            last_item = None
            for item in items:
                if item.experiment_id in filler \
                        or not last_item \
                        or last_item.experiment_id in filler \
                        or last_item.experiment_id != item.experiment_id:
                    slots.append(item.experiment_id)
                else:
                    colliding.append(item)
                last_item = item
            resolution_failed = False
            for item in colliding:
                slot_size = len(slots)
                n_insert_tries =  int(slot_size / 4)
                while n_insert_tries:
                    pos = random.SystemRandom().randint(0, slot_size - 2)
                    if item.experiment_id != slots[pos] and item.experiment_id != slots[pos + 1]:
                        slots.insert(pos + 1, item.experiment_id)
                        break
                    n_insert_tries -= 1
                if not n_insert_tries:
                    resolution_failed = True
            if not resolution_failed:
                return slots
            else:
                n_tries -= 1
        raise RuntimeError('Unable to compute slots')

    @cached_property
    def _item_list_items(self):
        item_lists = self.item_lists.all()
        items = item_models.Item.objects.filter(itemlist__in=item_lists).order_by('experiment_id')
        items = sorted(items, key=lambda x: x.experiment_block)
        return list(items)

    def _compute_slots(self, experiments, block_randomization):
        slots = {}
        items_by_block = groupby(self._item_list_items, lambda x: x.experiment_block)
        for block, block_items in items_by_block:
            block_items = list(block_items)
            if block_randomization[block] == QuestionnaireBlock.RANDOMIZATION_PSEUDO:
                slots[block] = self._compute_block_slots(block_items, experiments)
        return slots

    def _random_question_permutations(self, n_items):
        questions = [question.number for question in self.study.questions]
        question_permutations = list(permutations(questions))
        n_permutations = len(question_permutations)
        per_permutation = ceil(n_items/n_permutations)
        question_permutations = per_permutation*question_permutations
        random.SystemRandom().shuffle(question_permutations)
        return question_permutations

    def _randomize_question_order(self, questionnaire_items):
        n_items = len(questionnaire_items)
        question_permutations = self._random_question_permutations(n_items)
        for questionnaire_item, permutation in zip(questionnaire_items, question_permutations):
            questionnaire_item.question_order = ','.join(str(p) for p in permutation)

    def generate_items(self, experiments=None):
        if not experiments:
            experiments = {e.id: e for e in experiment_models.Experiment.objects.filter(study=self.study)}
        block_randomization = self._block_randomization()
        slots = self._compute_slots(experiments, block_randomization)
        items_by_block = groupby(self._item_list_items, lambda x: x.experiment_block)
        block_offset = 0
        questionnaire_items = []
        for block, block_items in items_by_block:
            block_items = list(block_items)
            if block_randomization[block] == QuestionnaireBlock.RANDOMIZATION_TRUE:
                questionnaire_items.extend(self._generate_items_random(block_items, block_offset))
            elif block_randomization[block] == QuestionnaireBlock.RANDOMIZATION_PSEUDO:
                questionnaire_items.extend(
                    self._generate_items_pseudo_random(block_items, block_offset, slots[block], experiments)
                )
            else:
                questionnaire_items.extend(self._generate_block_items(block_items, block_offset))
            block_offset += len(block_items)
        if self.study.pseudo_randomize_question_order:
            self._randomize_question_order(questionnaire_items)
        QuestionnaireItem.objects.bulk_create(questionnaire_items)

    def __str__(self):
        return str(self.number)


class QuestionnaireBlock(models.Model):
    block = models.IntegerField()
    instructions = MarkdownxField(
        max_length=5000,
        help_text='These instructions will be presented to the participant before the experiment begins.',
        blank=True,
        null=True,
    )
    RANDOMIZATION_PSEUDO = 'pseudo'
    RANDOMIZATION_NONE = 'none'
    RANDOMIZATION_TRUE = 'true'
    RANDOMIZATION_TYPE = (
        (RANDOMIZATION_PSEUDO, 'Pseudo-randomize'),
        (RANDOMIZATION_NONE, 'Keep item order'),
        (RANDOMIZATION_TRUE, 'Randomize'),
    )
    randomization = models.CharField(
        max_length=8,
        choices=RANDOMIZATION_TYPE,
        default=RANDOMIZATION_PSEUDO,
        help_text='Randomize items in each questionnaire block',
        blank=True,
    )
    study = models.ForeignKey(
        'lrex_study.Study',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['block']

    def __str__(self):
        return str(self.block)


class QuestionnaireItem(models.Model):
    number = models.IntegerField()
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    item = models.ForeignKey(item_models.Item, on_delete=models.CASCADE)
    question_order = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['number']

    @cached_property
    def question_order_user(self):
        return ','.join(str(int(question_num) + 1) for question_num in self.question_order.split(','))

    def __str__(self):
        return '{} - {}'.format(self.number, self.item)


class TrialStatus(Enum):
    CREATED = 1
    STARTED = 2
    FINISHED = 3
    ABANDONED = 4


class Trial(models.Model):
    slug = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    created = models.DateTimeField(
        default=timezone.now
    )
    subject_id = models.CharField(
        max_length=200,
        help_text='Provide an identification number/name (as instructed by the experimenter).',
        verbose_name='ID',
    )
    rating_proof = models.CharField(
        max_length=8,
        blank=True,
        null=True,
    )
    is_test = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ['created']

    def save(self, *args, **kwargs):
        if not self.subject_id:
            if Trial.objects.filter(questionnaire__study=self.questionnaire.study, is_test=False).exists():
                last_trial = Trial.objects.filter(questionnaire__study=self.questionnaire.study, is_test=False).last()
                try:
                    self.subject_id = int(last_trial.subject_id) + 1
                except ValueError:
                    self.subject_id = 1
            else:
                self.subject_id = 1
        return super().save(*args, **kwargs)

    @cached_property
    def items(self):
        return self.questionnaire.items

    @cached_property
    def questionnaire_item_ratings(self):
        item_ratings = []
        for questionnaire_item in self.questionnaire.questionnaireitem_set.all():
            ratings = Rating.objects.filter(trial=self, questionnaire_item=questionnaire_item).all()
            item_ratings.append((questionnaire_item, ratings))
        return item_ratings

    @cached_property
    def ratings_completed(self):
        return Rating.objects.filter(trial=self, question=0).count()

    ABANDONED_AFTER_HRS = 1

    @property
    def status(self):
        if self.ratings_completed > 0:
            n_items = len(self.items)
            if self.ratings_completed == n_items:
                return TrialStatus.FINISHED
            if self.created + timedelta(hours=self.ABANDONED_AFTER_HRS) < timezone.now():
                return TrialStatus.ABANDONED
            return TrialStatus.STARTED
        else:
            if self.created + timedelta(hours=self.ABANDONED_AFTER_HRS) < timezone.now():
                return TrialStatus.ABANDONED
        return TrialStatus.CREATED

    def init(self, study):
        self.questionnaire = study.next_questionnaire(is_test=self.is_test)
        self.save()

    def generate_rating_proof(self):
        if self.rating_proof:
            return self.rating_proof
        if self.status == TrialStatus.FINISHED:
            self.rating_proof = ''.join(
                random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8)
            )
            self.save()
            return self.rating_proof
        return None

    def get_absolute_url(self):
        return reverse('trial', args=[self.slug])

    def __str__(self):
        return '{} trial'.format(self.subject_id)


class Rating(models.Model):
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE)
    questionnaire_item = models.ForeignKey(QuestionnaireItem, on_delete=models.CASCADE)
    question = models.IntegerField(default=0)
    scale_value = models.ForeignKey(study_models.ScaleValue, on_delete=models.CASCADE)

    class Meta:
        ordering = ['trial', 'questionnaire_item', 'question']
