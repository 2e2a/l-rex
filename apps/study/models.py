import csv
import io
import re
import zipfile
from collections import OrderedDict
from itertools import groupby
from markdownx.models import MarkdownxField

from enum import Enum
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import mark_safe
from django.utils.dateformat import format
from django.utils.timezone import now

from apps.contrib import csv as contrib_csv
from apps.contrib import math
from apps.contrib.utils import slugify_unique
from apps.contrib.utils import split_list_string, to_list_string


class StudySteps(Enum):
    STEP_STD_QUESTION_CREATE = 1
    STEP_STD_INSTRUCTIONS_EDIT = 2
    STEP_STD_INTRO_EDIT = 3
    STEP_STD_EXP_CREATE = 4
    STEP_STD_QUESTIONNAIRES_GENERATE = 5
    STEP_STD_CONTACT_ADD = 6
    STEP_STD_CONSENT_ADD = 7
    STEP_STD_PUBLISH = 8
    STEP_STD_FINISH = 9
    STEP_STD_RESULTS = 10
    STEP_STD_ANONYMIZE = 11
    STEP_STD_ARCHIVE = 12
    STEP_STD_OPT_DRAFT = 13
    STEP_STD_OPT_PUBLISH = 14
    STEP_STD_OPT_BLOCK_INSTRUCTIONS = 15
    STEP_STD_OPT_SETTINGS = 16
    STEP_STD_OPT_LABELS = 17
    STEP_STD_OPT_SHARE = 18
    STEP_STD_OPT_INVOICE = 19


class Study(models.Model):
    title = models.CharField(
        max_length=100,
        help_text='Give your study a name.',
    )
    slug = models.SlugField(
        unique=True,
        max_length=110,
    )
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ITEM_TYPE_TXT = 'txt'
    ITEM_TYPE_MARKDOWN = 'mkd'
    ITEM_TYPE_AUDIO_LINK = 'aul'
    ITEM_TYPE = (
        (ITEM_TYPE_TXT, 'Plain text'),
        (ITEM_TYPE_MARKDOWN, 'Rich text with markdown'),
        (ITEM_TYPE_AUDIO_LINK, 'Audio links'),
    )
    item_type = models.CharField(
        max_length=3,
        choices=ITEM_TYPE,
        default=ITEM_TYPE_TXT,
        help_text='The items can be plain text or markdown rich text or links to audio files (self-hosted).',
    )
    use_blocks = models.BooleanField(
        default=False,
        help_text='Enable if you want to divide the questionnaire into separate parts (blocks) with individual '
                  'instructions.',
    )
    pseudo_randomize_question_order = models.BooleanField(
        default=False,
        help_text='Show questions in random order (if multiple questions are defined).',
    )
    use_vertical_scale_layout = models.BooleanField(
        default=False,
        help_text=(
            'Enable if you want the response options to be presented below each other (default: horizontal layout). '
            'If multiple questions are defined, this setting applies to all of them.'
        ),
    )
    enable_item_rating_feedback = models.BooleanField(
        default=False,
        help_text='Allows you to define feedback shown to participants for individual item ratings.',
    )
    password = models.CharField(
        blank=True,
        null=True,
        max_length=200,
        help_text='This password will be required to participate in the study.',
    )
    PARTICIPANT_ID_NONE = 'none'
    PARTICIPANT_ID_ENTER = 'enter'
    PARTICIPANT_ID_RANDOM = 'random'
    PARTICIPANT_ID_CHOICES = (
        (PARTICIPANT_ID_NONE, 'No participant IDs'),
        (PARTICIPANT_ID_ENTER, 'Participants have an external ID'),
        (PARTICIPANT_ID_RANDOM, 'Generate random ID for each participant'),
    )
    participant_id = models.CharField(
        max_length=8,
        choices=PARTICIPANT_ID_CHOICES,
        default=PARTICIPANT_ID_NONE,
        help_text=mark_safe(
            'Choose the first option for fully anonymous participation. Choose the second option if you want to '
            'save an ID that participants receive independently (e.g., from an external participant recruitment '
            'platform). The ID is entered manually or passed via an URL parameter '
            '(see <a target="_blank" href="https://github.com/2e2a/l-rex/wiki">Wiki&#8599;</a> for details). '
            'Choose the third option to generate a unique identifier (code) for each participant which will be '
            'displayed at the end of the questionnaire and which can be used e.g. as proof of participation.'
        ),
        verbose_name='participant ID'
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        help_text='Set a participation deadline.'
    )
    trial_limit = models.IntegerField(
        null=True,
        blank=True,
        help_text='If you want to set a maximal number of participants, enter a number.',
        verbose_name='Maximal number of participants',
    )
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='shared_studies',
        help_text='Give other users access to the study.',
    )
    instructions = MarkdownxField(
        blank=True,
        null=True,
        max_length=5000,
        help_text='These instructions will be presented to the participant before the experiment begins.',
    )
    short_instructions = MarkdownxField(
        blank=True,
        null=True,
        max_length=3000,
        help_text='You can optionally provide a shorter version of the instructions that the participant can access at '
                  'any point during participation as a reminder of the task.'
    )
    contact_name = models.CharField(
        null=True,
        blank=True,
        max_length=1000,
        help_text='This name will be shown to participants as part of the contact information '
                  'before the study begins.',
    )
    contact_email = models.EmailField(
        null=True,
        blank=True,
        help_text='This e-mail address will be shown to participants as part of the contact information '
                  'before the study begins.',
    )
    contact_affiliation = models.CharField(
        null=True,
        blank=True,
        max_length=1000,
        help_text='This affiliation (e.g., university or research institute) will be shown to participants'
                  ' as part of the contact information before the study begins.',
    )
    contact_details = MarkdownxField(
        blank=True,
        null=True,
        max_length=5000,
        help_text='You can optionally provide additional information about you and/or the research project '
                  '(e.g., "This study is part of the research project XY, for more information, see ..."). '
                  'This information will be shown to participants before the study begins.'
    )
    consent_form_text = MarkdownxField(
        null=True,
        blank=True,
        max_length=5000,
        help_text=(
            'This text informs participants about the procedure and '
            'purpose of the study. It will be shown to the participants before the '
            'study begins. It should include a privacy statement: whether any '
            'personal data is collected and how it will be processed and stored.'
        )
    )
    consent_statement = models.CharField(
        max_length=500,
        default='I have read and understood the above information. I agree to participate in this study.',
        help_text='Participants will have to check a box with this statement before study begins.',
    )
    intro = MarkdownxField(
        blank=True,
        null=True,
        max_length=5000,
        help_text='This text will be presented to the participants on the first page.',
    )
    outro = MarkdownxField(
        blank=True,
        null=True,
        max_length=5000,
        help_text='This text will be presented to the participants on the last page.',
    )
    continue_label = models.CharField(
        max_length=40,
        default='Continue',
        help_text='Label of the "Continue" button used during participation.',
    )
    save_consent_form_label = models.CharField(
        max_length=40,
        default='Save this page',
        help_text='Label of the button used to save/print the consent form.',
    )
    consent_form_label = models.CharField(
        max_length=40,
        default='Consent form',
        help_text='Label for "Consent form" used during participation.',
    )
    contact_label = models.CharField(
        max_length=40,
        default='Contact',
        help_text='Label for "Contact" used during participation.',
    )
    instructions_label = models.CharField(
        max_length=60,
        default='Show/hide short instructions',
        help_text='Label of the link to the short instructions that the participant can access during participation '
                  '(if defined).',
    )
    block_instructions_label = models.CharField(
        max_length=60,
        default='Show/hide short instructions for this block',
        help_text='Label of the link to the short block instructions that the participant can access during  '
                  'participation (if defined).',
    )
    optional_label = models.CharField(
        max_length=40,
        default='optional',
        help_text='Label used for user input fields that can be optional, e.g. comment.',
    )
    comment_label = models.CharField(
        max_length=40,
        default='Comment',
        help_text='Label used for the comment field.',
    )
    participation_id_label = models.CharField(
        max_length=40,
        default='Participation ID',
        help_text=(
            'Label used for the participant ID form on the instruction page or for the participation code on the outro '
            'page, depending on the "participant ID" setting.'
        ),
        verbose_name='Participation ID label',
    )
    password_label = models.CharField(
        max_length=40,
        default='Password',
        help_text='Label used for the participant password form on the instruction page.'
    )
    answer_questions_message = models.CharField(
        max_length=500,
        default='Please answer all questions.',
        help_text='Error message shown to participant if a question was not answered.',
    )
    field_required_message = models.CharField(
        max_length=500,
        default='This field is required.',
        help_text=(
            'Error message shown to participant if a required field was not submitted. '
            'Used for e.g. questions, comments, demographics.'
        ),
    )
    feedback_message = models.CharField(
        max_length=500,
        default='Please note the following feedback.',
        help_text='Message indicating that feedback is shown for some ratings.',
    )
    is_published = models.BooleanField(
        default=False,
        help_text='Enable to publish your study. It will then be available for participation.',
    )
    is_finished = models.BooleanField(
        default=False,
        help_text='Enable to finish study participation.',
    )
    created_date = models.DateField(
        default=now,
        editable=False,
    )
    is_archived = models.BooleanField(
        default=False,
    )
    has_invoice = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ['-created_date', 'title']
        verbose_name_plural = 'Studies'

    def save(self, *args, **kwargs):
        new_slug = slugify_unique(self.title, Study, self.id)
        slug_changed = False
        if self.slug != new_slug:
            self.slug = new_slug
            slug_changed = True
        super().save(*args, **kwargs)
        if slug_changed:
            for materials in self.materials.all():
                materials.save()
            for questionnaire in self.questionnaires.all():
                questionnaire.save()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('study', args=[self.slug])

    @cached_property
    def shared_with_string(self):
        return to_list_string(self.shared_with.all())

    @cached_property
    def has_text_items(self):
        return self.item_type == self.ITEM_TYPE_TXT

    @cached_property
    def has_markdown_items(self):
        return self.item_type == self.ITEM_TYPE_MARKDOWN

    @cached_property
    def has_audiolink_items(self):
        return self.item_type == self.ITEM_TYPE_AUDIO_LINK

    @cached_property
    def item_blocks(self):
        item_blocks = set()
        for materials in self.materials.all():
            item_blocks.update(materials.item_blocks)
        return sorted(item_blocks)

    @cached_property
    def question(self):
        return self.questions.first()

    def get_question(self, number):
        for question in self.questions.all():
            if question.number == number:
                return question

    @cached_property
    def is_multi_question(self):
        return self.questions.count() > 1

    @cached_property
    def has_question_with_random_scale(self):
        return any(question.randomize_scale for question in self.questions.all())

    @cached_property
    def has_question_rating_comments(self):
        return self.questions.filter(
            rating_comment__in=[Question.RATING_COMMENT_OPTIONAL, Question.RATING_COMMENT_REQUIRED]
        ).exists()

    @cached_property
    def has_demographics(self):
        return self.demographics.exists()

    @cached_property
    def demographics_string(self):
        return to_list_string(field.name for field in self.demographics.all())

    @cached_property
    def has_items(self):
        from apps.item.models import Item
        return Item.objects.filter(materials__study=self).exists()

    @cached_property
    def has_item_questions(self):
        from apps.item.models import Item, ItemQuestion
        try:
            materials_items = Item.objects.filter(materials__study=self).all()
            return ItemQuestion.objects.filter(item__in=materials_items).exists()
        except Item.DoesNotExist:
            return False

    @cached_property
    def has_block_instructions(self):
        if not self.questionnaire_blocks.exists():
            return False
        for block in self.questionnaire_blocks.all():
            if not block.instructions:
                return False
        return True

    @cached_property
    def has_item_lists(self):
        return any(materials.has_lists for materials in self.materials.all())

    @cached_property
    def is_active(self):
        return self.is_published or self.trial_count > 0

    @cached_property
    def is_time_limit_reached(self):
        return self.end_date and self.end_date < timezone.now().date()

    @cached_property
    def is_trial_limit_reached(self):
        return self.trial_limit and self.trial_limit <= self.trial_count

    @cached_property
    def is_limit_reached(self):
        return self.is_time_limit_reached or self.is_trial_limit_reached

    @cached_property
    def trials(self):
        from apps.trial.models import Trial
        return Trial.objects.filter(questionnaire__study=self, is_test=False)

    @cached_property
    def trial_count(self):
        return self.trials.count()

    @cached_property
    def trial_count_test(self):
        from apps.trial.models import Trial
        return Trial.objects.filter(questionnaire__study=self, is_test=True).count()

    @cached_property
    def trial_count_active(self):
        return len([trial for trial in self.trials if not trial.is_finished and not trial.is_abandoned])

    @cached_property
    def trial_count_finished(self):
        return len([trial for trial in self.trials if trial.is_finished])

    @cached_property
    def trial_count_abandoned(self):
        return len([trial for trial in self.trials if trial.is_abandoned])

    def delete_abandoned_trials(self):
        trials_abandoned = [trial for trial in self.trials if trial.is_abandoned]
        for trial in trials_abandoned:
            trial.delete()

    def delete_test_trials(self):
        from apps.trial.models import Trial
        Trial.objects.filter(questionnaire__study=self, is_test=True).delete()

    @property
    def has_participant_information(self):
        from apps.trial.models import Trial
        return Trial.objects.filter(
            questionnaire__study=self,
            is_test=False,
        ).exclude(
            participant_id=None,
            demographics=None,
        ).exists()

    def delete_participant_information(self):
        from apps.trial.models import Trial, DemographicValue
        Trial.objects.filter(questionnaire__study=self).update(participant_id=None)
        DemographicValue.objects.filter(trial__questionnaire__study=self).delete()

    @cached_property
    def is_allowed_create_questionnaires(self):
        if not self.materials.exists():
            return False
        for materials in self.materials.all():
            if not materials.is_complete:
                return False
        return True

    @cached_property
    def is_allowed_publish(self):
        return (
            self.questions.exists() and self.instructions and self.intro and self.consent_form_text
            and self.items_validated and self.questionnaires.exists()
        )

    @cached_property
    def is_allowed_pseudo_randomization(self):
        return self.materials.filter(is_filler=True).count() > 0

    @cached_property
    def items_validated(self):
        if not self.materials.exists():
            return False
        return not self.materials.filter(items_validated=False).exists()

    @cached_property
    def randomization_reqiured(self):
        from apps.trial.models import QuestionnaireBlock
        for questionnaire_block in self.questionnaire_blocks.all():
            if questionnaire_block.randomization != QuestionnaireBlock.RANDOMIZATION_NONE:
                return True
        return False

    @cached_property
    def block_randomization(self):
        block_randomization = {}
        questionnaire_blocks = self.questionnaire_blocks.all()
        for questionnaire_block in questionnaire_blocks:
            block_randomization[questionnaire_block.block] = questionnaire_block.randomization
        return block_randomization

    @cached_property
    def has_exmaples(self):
        return self.materials.filter(is_example=True).exists()

    @cached_property
    def has_questionnaires(self):
        return self.questionnaires.exists()

    @cached_property
    def questionnaire_length(self):
        first_questionnaire = self.questionnaires.first()
        if first_questionnaire:
            return first_questionnaire.questionnaire_items.count()
        return 0

    def _questionnaire_trial_count(self, is_test=False):
        from apps.trial.models import Trial
        questionnaires = self.questionnaires.all()
        trials = Trial.objects.filter(
            questionnaire_id__in=[questionnaire.id for questionnaire in questionnaires],
            is_test=is_test,
        ).order_by('questionnaire_id')
        trials_per_questionnaire = groupby(trials, lambda x: x.questionnaire_id)
        trial_count_by_id = {q_id: len(list(q_trials)) for q_id, q_trials in trials_per_questionnaire}
        trial_count = {}
        for questionnaire in questionnaires:
            trial_count.update({questionnaire: trial_count_by_id.get(questionnaire.id, 0)})
        return trial_count

    def next_questionnaire(self, is_test=False):
        trial_count = self._questionnaire_trial_count(is_test)
        next_questionnaire = min(trial_count, key=trial_count.get)
        return next_questionnaire

    def _questionnaire_count(self, materials_list):
        questionnaire_lcm = 1
        for materials in materials_list:
            questionnaire_lcm = math.lcm(questionnaire_lcm,  materials.condition_count)
        return questionnaire_lcm

    def _init_questionnaire_lists(self, materials_list):
        questionnaire_item_list = []
        for materials in materials_list:
            item_list = materials.lists.first()
            questionnaire_item_list.append(item_list)
        return questionnaire_item_list

    def _next_questionnaire_lists(self, item_lists_by_materials, last_item_lists):
        questionnaire_item_list = []
        for last_item_list in last_item_lists:
            materials_item_lists = item_lists_by_materials[last_item_list.materials_id]
            next_item_list = (
                materials_item_lists[last_item_list.number + 1]
                if (last_item_list.number + 1) < len(materials_item_lists) else materials_item_lists[0]
            )
            questionnaire_item_list.append(next_item_list)
        return questionnaire_item_list

    def _initial_questionnaires(self, materials):
        from apps.trial.models import Questionnaire
        questionnaires = []
        questionnaire_count = self._questionnaire_count(materials)
        for i in range(1, questionnaire_count + 1):
            slug = Questionnaire.compute_slug(self, i)
            questionnaires.append(Questionnaire(study=self, number=i, slug=slug))
        return questionnaires

    def _get_item_lists_by_materials(self, materials_list):
        item_lists_by_materials = {}
        for materials in materials_list:
            item_lists_by_materials[materials.pk] = list(materials.lists.all())
        return item_lists_by_materials

    def _compute_questionnaire_item_lists(self, materials, item_lists_by_materials, questionnaires):
        item_lists_by_questionnaire = {}
        last_item_lists = None
        for questionnaire in questionnaires:
            questionnaire_item_lists = (
                self._init_questionnaire_lists(materials)
                if not last_item_lists
                else self._next_questionnaire_lists(item_lists_by_materials, last_item_lists)
            )
            questionnaire.item_lists.set(questionnaire_item_lists)
            last_item_lists = questionnaire_item_lists
            item_lists_by_questionnaire[questionnaire] = questionnaire_item_lists
        return item_lists_by_questionnaire

    def _generate_questionnaire_permutations(self, materials, questionnaires, permutations=3):
        from apps.trial.models import Questionnaire, QuestionnaireItem
        questionnaire_permutations = []
        if self.randomization_reqiured:
            questionnaire_count = len(questionnaires)
            for i, questionnaire in enumerate(questionnaires):
                for permutation in range(1, permutations + 1):
                    num = questionnaire_count * permutation + i + 1
                    slug = Questionnaire.compute_slug(self, num)
                    questionnaire_permutations.append(Questionnaire(study=self, number=num, slug=slug))
        return questionnaire_permutations

    def _items_by_block_by_questionnaire(self, materials_list, questionnaires, lists_by_questionnaire, use_blocks):
        from apps.item.models import Item
        items_by_block_by_questionnaire = {}
        items = Item.objects.filter(materials__study=self).order_by('materials', 'number', 'condition')
        items = list(items.prefetch_related('itemlist_set').all())
        for questionnaire in questionnaires:
            items_in_questionnaire = []
            for item in items:
                if set(item.itemlist_set.all()).intersection(lists_by_questionnaire[questionnaire]):
                    items_in_questionnaire.append(item)
            items_by_block = {}
            if use_blocks:
                materials_block = {materials.pk: materials.auto_block for materials in materials_list}
                for item in items_in_questionnaire:
                    block = materials_block[item.materials_id]
                    if block is None:
                        block = item.block
                    items_by_block.setdefault(block, [])
                    items_by_block[block].append(item)
            else:
                items_by_block[1] = list(items_in_questionnaire)
            items_by_block_by_questionnaire[questionnaire] = items_by_block
        return items_by_block_by_questionnaire

    def generate_questionnaires(self):
        from apps.trial.models import Questionnaire, QuestionnaireItem, QuestionProperty
        try:
            self.questionnaires.all().delete()
            materials_list = list(self.materials.prefetch_related('items', 'lists').all())
            item_lists_by_materials = self._get_item_lists_by_materials(materials_list)
            questionnaires = self._initial_questionnaires(materials_list)
            randomize_scales = self.has_question_with_random_scale
            questions = list(self.questions.all())
            if self.randomization_reqiured:
                questionnaires.extend(self._generate_questionnaire_permutations(materials_list, questionnaires))
            questionnaires = Questionnaire.objects.bulk_create(questionnaires)
            lists_by_questionnaire = self._compute_questionnaire_item_lists(
                materials_list, item_lists_by_materials, questionnaires
            )
            items_by_block = self._items_by_block_by_questionnaire(
                materials_list, questionnaires, lists_by_questionnaire, self.use_blocks
            )
            all_questionnaires = []
            questionnaire_items_by_questionnaire = {}
            for questionnaire in questionnaires:
                questionnaire_items = questionnaire.generate_questionnaire_items(
                    self, materials_list, items_by_block[questionnaire], self.block_randomization
                )
                if self.pseudo_randomize_question_order:
                    questionnaire.randomize_question_order(questions, questionnaire_items)
                questionnaire_items_by_questionnaire[questionnaire] = questionnaire_items
                all_questionnaires.extend(questionnaire_items)
            QuestionnaireItem.objects.bulk_create(all_questionnaires)
            question_properties = []
            for questionnaire, questionnaire_items in questionnaire_items_by_questionnaire.items():
                if randomize_scales:
                    question_properties.extend(
                        questionnaire.generate_question_properties(questions, questionnaire_items)
                    )
            QuestionProperty.objects.bulk_create(question_properties)
        except RuntimeError as error:
            self.delete_questionnaires()
            raise error

    def delete_questionnaires(self):
        from apps.trial.models import Trial
        Trial.objects.filter(questionnaire__study=self).all().delete()
        self.questionnaires.all().delete()

    def delete_questionnaire_blocks(self):
        self.questionnaire_blocks.all().delete()

    @cached_property
    def contact(self):
        return '{}, {}{}'.format(
            self.contact_name,
            '{}, '.format(self.contact_affiliation) if self.contact_affiliation else '',
            self.contact_email,
            self.contact_email,
        )

    def participant_information_csv(self, fileobj):
        from apps.trial.models import Trial
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        csv_row = ['participant', 'id', 'trial start utc', 'trial end utc', 'time taken sec']
        if self.has_demographics:
            csv_row.extend(
                'demographic{}'.format(i) for i, demographic_field in enumerate(self.demographics.all(), 1)
            )
        writer.writerow(csv_row)
        trials = Trial.objects.filter(questionnaire__study=self, is_test=False)
        if self.has_demographics:
            trials = trials.prefetch_related('demographics')
        for i, trial in enumerate(trials, 1):
            csv_row = [
                i,
                trial.participant_id,
                format(trial.created, 'Y-m-d H:i:s') if trial.created else '',
                format(trial.ended, 'Y-m-d H:i:s') if trial.ended else '',
                trial.time_taken,
            ]
            if self.has_demographics:
                csv_row.extend(demographic_value.value for demographic_value in trial.demographics.all())
            writer.writerow(csv_row)

    @property
    def ARCHIVE_FILES(self):
        return [
            ('01_results.csv', self.results_csv, None,
             'Study results'),
            ('02_settings.csv', self.settings_csv, self.settings_from_csv,
             'General study settings, instructions, intro/outro, etc.'),
            ('03_questions.csv', self.questions_csv, self.questions_from_csv,
             'Questions'),
            ('04_materials.csv', self.materials_csv, self.materials_from_csv,
             'Settings for each set of materials'),
            ('05_items.csv', self.items_csv, self.items_from_csv,
             'Items for all sets of materials'),
            ('06_item_feedbacks.csv', self.item_feedbacks_csv, self.item_feedbacks_from_csv,
             'Item feedback (if used)'),
            ('07_lists.csv', self.itemlists_csv, self.itemlists_from_csv,
             'Lists for all sets of materials'),
            ('08_questionnaires.csv', self.questionnaires_csv, self.questionnaires_from_csv,
             'Study questionnaires'),
            ('09_blocks.csv', self.questionnaire_blocks_csv, self.questionnaire_blocks_from_csv,
             'Questionnaire blocks (if used)'),
        ]

    SETTING_FIELDS = [
        'title',
        'item_type',
        'use_blocks',
        'pseudo_randomize_question_order',
        'enable_item_rating_feedback',
        'password',
        'participant_id',
        'end_date',
        'trial_limit',
        'instructions',
        'short_instructions',
        'contact_name',
        'contact_email',
        'contact_affiliation',
        'contact_details',
        'consent_form_text',
        'consent_statement',
        'intro',
        'outro',
        'continue_label',
        'save_consent_form_label',
        'consent_form_label',
        'contact_label',
        'instructions_label',
        'block_instructions_label',
        'optional_label',
        'comment_label',
        'answer_questions_message',
        'feedback_message',
    ]

    SETTING_BOOL_FIELDS = [
        'use_blocks',
        'pseudo_randomize_question_order',
    ]

    def _read_settings(self, reader):
        study_settings = {}
        for row in reader:
            if len(row) == 2:
                study_settings.update({row[0]: row[1]})
        return study_settings

    def results_csv(self, fileobj):
        for i, materials in enumerate(self.materials.all()):
            if i == 0:
                writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
                header = materials.results_csv_header()
                writer.writerow(header)
            materials.results_csv(fileobj)

    def settings_csv(self, fileobj):
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        writer.writerow(['version', settings.LREX_VERSION])
        for setting_field in self.SETTING_FIELDS:
            writer.writerow([setting_field, getattr(self, setting_field)])
        writer.writerow(
            ['shared_with', self.shared_with_string]
        )
        writer.writerow(
            ['demographics', self.demographics_string]
        )

    def settings_from_csv(self, fileobj):
        reader = csv.reader(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        study_settings = self._read_settings(reader)
        if not self.is_archived:
            for field in self.SETTING_FIELDS:
                if field in study_settings and study_settings[field]:
                    if field not in self.SETTING_BOOL_FIELDS:
                        setattr(self, field, study_settings[field])
                    else:
                        setattr(self, field, study_settings[field] == 'True')

            self.save()
        shared_with_user_names = split_list_string(study_settings['shared_with'])
        shared_with_users = User.objects.filter(username__in=shared_with_user_names)
        self.shared_with.set(shared_with_users)
        for demographics_field in split_list_string(study_settings['demographics']):
            self.demographics.create(name=demographics_field)
        self.created_date = now().date()
        self.is_published = False
        self.is_archived = False
        self.is_finished = False
        self.save()

    def questions_csv_header(self, **kwargs):
        return ['question', 'scale_labels', 'legend', 'randomize_scale', 'rating_comment']

    def questions_csv(self, fileobj):
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        header = self.questions_csv_header()
        writer.writerow(header)
        for question in self.questions.all():
            writer.writerow([
                question.question,
                question.get_scale_labels(),
                question.legend,
                question.randomize_scale,
                question.rating_comment,
            ])

    def questions_from_csv(self, fileobj, detected_csv=contrib_csv.DEFAULT_DIALECT):
        scale_values = []
        columns = contrib_csv.csv_columns(self.questions_csv_header)
        reader = csv.reader(fileobj, delimiter=detected_csv['delimiter'], quoting=detected_csv['quoting'])
        if detected_csv['has_header']:
            next(reader)
        question_number = 0
        for row in reader:
            if not row:
                continue
            question = Question.objects.create(
                study=self,
                number=question_number,
                question=row[columns['question']],
                legend=row[columns['legend']],
                randomize_scale=(row[columns['randomize_scale']] == 'True'),
                rating_comment=row[columns['rating_comment']],
            )
            for i, scale_value in enumerate(split_list_string(row[columns['scale_labels']])):
                scale_values.append(
                    ScaleValue(
                        number=i,
                        question=question,
                        label=scale_value,
                    )
                )
            question_number += 1
        ScaleValue.objects.bulk_create(scale_values)

    def materials_csv_header(self, **kwargs):
        return ['title', 'list_distribution', 'is_filler', 'is_example', 'block', 'items_validated']

    def materials_csv(self, fileobj):
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        header = self.materials_csv_header()
        writer.writerow(header)
        for materials in self.materials.all():
            writer.writerow([
                materials.title,
                materials.item_list_distribution,
                materials.is_filler,
                materials.is_example,
                materials.block,
                materials.items_validated,
            ])

    def materials_from_csv(self, fileobj, detected_csv=contrib_csv.DEFAULT_DIALECT):
        columns = contrib_csv.csv_columns(self.materials_csv_header)
        reader = csv.reader(fileobj, delimiter=detected_csv['delimiter'], quoting=detected_csv['quoting'])
        if detected_csv['has_header']:
            next(reader)
        for row in reader:
            if not row:
                continue
            materials = self.materials.create(
                title=row[columns['title']],
                item_list_distribution=row[columns['list_distribution']],
                is_filler=(row[columns['is_filler']] == 'True'),
                is_example=(row[columns['is_example']] == 'True'),
                block=row[columns['block']],
                items_validated=(row[columns['items_validated']] == 'True'),
            )
            materials.save()

    def items_csv(self, fileobj):
        for i, materials in enumerate(self.materials.all()):
            if i == 0:
                writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
                header = materials.items_csv_header(add_materials_column=True)
                writer.writerow(header)
            materials.items_csv(fileobj, add_header=False, add_materials_column=True)

    def items_from_csv(self, fileobj, **kwargs):
        for materials in self.materials.all():
            fileobj.seek(0)
            materials.items_from_csv(fileobj, has_materials_column=True)

    def itemlists_csv(self, fileobj):
        for i, materials in enumerate(self.materials.all()):
            if i == 0:
                writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
                header = materials.itemlists_csv_header(add_materials_column=True)
                writer.writerow(header)
            materials.itemlists_csv(fileobj, add_header=False, add_materials_column=True)

    def itemlists_from_csv(self, fileobj, **kwargs):
        for materials in self.materials.all():
            fileobj.seek(0)
            materials.itemlists_from_csv(fileobj, has_materials_column=True)

    def questionnaires_csv_header(self, **kwargs):
        return ['questionnaire', 'lists', 'items', 'question_order']

    def questionnaires_csv(self, fileobj):
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        header = self.questionnaires_csv_header()
        writer.writerow(header)
        for questionnaire in self.questionnaires.all():
            csv_row = [
                questionnaire.number,
                ','.join(['{}-{}'.format(item_list.materials.title, item_list.number)
                          for item_list in questionnaire.item_lists.all()]),
                ','.join(['{}-{}'.format(item.materials.title, item) for item in questionnaire.items]),
            ]
            if self.pseudo_randomize_question_order:
                csv_row.append(
                    ','.join('"{}"'.format(q_item.question_order) for q_item in questionnaire.questionnaire_items.all())
                )
            else:
                csv_row.append('')
            writer.writerow(csv_row)

    def questionnaires_from_csv(self, fileobj, user_columns=None, detected_csv=contrib_csv.DEFAULT_DIALECT):
        # FIXME: handle validation error?
        from apps.item.models import Item, ItemList
        from apps.trial.models import Questionnaire, QuestionnaireItem
        from apps.trial.forms import QuestionnaireUploadForm
        questionnaire_items = []
        self.delete_questionnaires()
        reader = csv.reader(fileobj, delimiter=detected_csv['delimiter'], quoting=detected_csv['quoting'])
        if detected_csv['has_header']:
            next(reader)
        columns = contrib_csv.csv_columns(self.questionnaires_csv_header, user_columns=user_columns)
        materials_titles = { materials.pk: materials.title for materials in self.materials.all()}
        study_items = list(Item.objects.filter(materials__study=self).all())
        study_itemlists = list(ItemList.objects.filter(materials__study=self).all())
        for row in reader:
            if not row:
                continue
            questionnaire = Questionnaire.objects.create(study=self, number=row[columns['questionnaire']])
            if columns['lists'] > 0 and row[columns['lists']]:
                item_lists = QuestionnaireUploadForm.read_item_lists(
                    self, row[columns['lists']], materials_titles, study_itemlists
                )
                questionnaire.item_lists.set(item_lists)
            items = QuestionnaireUploadForm.read_items(row[columns['items']], materials_titles, study_items)
            if self.pseudo_randomize_question_order:
                question_orders = re.findall('"([^"]+)"', row[columns['question_order']])  # FIXME: why
            for i, item in enumerate(items):
                questionnaire_items.append(
                    QuestionnaireItem(
                        number=i,
                        questionnaire=questionnaire,
                        item=item,
                        question_order=question_orders[i] if self.pseudo_randomize_question_order else None,
                    )
                )
        QuestionnaireItem.objects.bulk_create(questionnaire_items)

    def questionnaire_blocks_csv_header(self, **kwargs):
        return ['block', 'randomization', 'instructions', 'short_instructions']

    def questionnaire_blocks_csv(self, fileobj):
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        header = self.questionnaire_blocks_csv_header()
        writer.writerow(header)
        for block in self.questionnaire_blocks.all():
            csv_row = [
                block.block,
                block.randomization,
                block.instructions,
                block.short_instructions,
            ]
            writer.writerow(csv_row)

    def questionnaire_blocks_from_csv(self, fileobj, user_columns=None, detected_csv=contrib_csv.DEFAULT_DIALECT):
        from apps.trial.models import QuestionnaireBlock
        self.delete_questionnaire_blocks()
        reader = csv.reader(fileobj, delimiter=detected_csv['delimiter'], quoting=detected_csv['quoting'])
        if detected_csv['has_header']:
            next(reader)
        columns = contrib_csv.csv_columns(self.questionnaire_blocks_csv_header, user_columns=user_columns)
        for row in reader:
            if not row:
                continue
            QuestionnaireBlock.objects.create(
                study=self,
                block=row[columns['block']],
                instructions=row[columns['instructions']],
                short_instructions=row[columns['short_instructions']],
                randomization=row[columns['randomization']] if 'randomization' in columns else None,
            )

    def item_feedbacks_csv(self, fileobj):
        for i, materials in enumerate(self.materials.all()):
            if i == 0:
                writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
                header = materials.item_feedbacks_csv_header(add_materials_column=True)
                writer.writerow(header)
            materials.item_feedbacks_csv(fileobj, add_header=False, add_materials_column=True)

    def item_feedbacks_from_csv(self, fileobj, **kwargs):
        for materials in self.materials.all():
            fileobj.seek(0)
            materials.item_feedbacks_from_csv(fileobj, has_materials_column=True)

    def archive_file(self, fileobj):
        with zipfile.ZipFile(fileobj, 'w', zipfile.ZIP_DEFLATED) as archive:
            file = io.StringIO()
            for archive_file, archive_func, _, _ in self.ARCHIVE_FILES:
                if archive_func:
                    file.truncate(0)
                    file.seek(0)
                    archive_func(file)
                    archive.writestr(archive_file, file.getvalue())

    def archive(self):
        self.delete_participant_information()
        self.delete_questionnaires()
        self.materials.all().delete()
        self.questions.all().delete()
        self.is_archived = True
        self.save()

    def restore_from_archive(self, fileiobj, detected_csv_dialect=None):
        with zipfile.ZipFile(fileiobj) as archive:
            try:
                for archive_file, _, restore_func, _  in self.ARCHIVE_FILES:
                    filename_without_num = archive_file[3:]
                    filename = None
                    for file_in_archive in archive.namelist():
                        if file_in_archive.endswith(filename_without_num):
                            filename = file_in_archive
                    if filename and restore_func:
                        with archive.open(archive_file, 'r') as file:
                            text_file = io.StringIO(file.read().decode())
                            restore_func(text_file)
            except Exception as err:
                if self.id:
                    self.delete()
                raise err

    @classmethod
    def create_from_archive_file(cls, fileobj, creator, detected_csv_dialect=None):
        study = cls()
        study.creator = creator
        study.restore_from_archive(fileobj, detected_csv_dialect=detected_csv_dialect)
        return study

    STEP_DESCRIPTION = {
        StudySteps.STEP_STD_QUESTION_CREATE: 'define a question',
        StudySteps.STEP_STD_INSTRUCTIONS_EDIT: 'write instructions',
        StudySteps.STEP_STD_INTRO_EDIT: 'create intro/outro',
        StudySteps.STEP_STD_EXP_CREATE: 'create materials',
        StudySteps.STEP_STD_QUESTIONNAIRES_GENERATE: 'generate questionnaires',
        StudySteps.STEP_STD_CONTACT_ADD: 'add contact information',
        StudySteps.STEP_STD_CONSENT_ADD: 'add consent form',
        StudySteps.STEP_STD_PUBLISH: 'set study status to published to start collecting results',
        StudySteps.STEP_STD_FINISH: 'set study status to finished when done',
        StudySteps.STEP_STD_RESULTS: 'download results',
        StudySteps.STEP_STD_ANONYMIZE: 'remove participant information when not needed anymore',
        StudySteps.STEP_STD_ARCHIVE: 'archive the study',
        StudySteps.STEP_STD_OPT_DRAFT: 'set study status to draft to make changes',
        StudySteps.STEP_STD_OPT_PUBLISH: 'set study status to publish to resume collecting results',
        StudySteps.STEP_STD_OPT_BLOCK_INSTRUCTIONS: 'write instructions for questionnaire blocks',
        StudySteps.STEP_STD_OPT_SETTINGS: 'customize study settings',
        StudySteps.STEP_STD_OPT_LABELS: 'customize labels',
        StudySteps.STEP_STD_OPT_SHARE: 'share study with other users',
        StudySteps.STEP_STD_OPT_INVOICE: 'request an invoice',
    }

    def step_url(self, step):
        if step == StudySteps.STEP_STD_QUESTION_CREATE:
            return reverse('study-questions', args=[self.slug])
        elif step == StudySteps.STEP_STD_INSTRUCTIONS_EDIT:
            return reverse('study-instructions', args=[self.slug])
        elif step == StudySteps.STEP_STD_INTRO_EDIT:
            return reverse('study-intro', args=[self.slug])
        elif step == StudySteps.STEP_STD_EXP_CREATE:
            return reverse('materials-create', args=[self.slug])
        elif step == StudySteps.STEP_STD_QUESTIONNAIRES_GENERATE:
            return reverse('questionnaires', args=[self.slug])
        elif step == StudySteps.STEP_STD_CONTACT_ADD:
            return reverse('study-contact', args=[self.slug])
        elif step == StudySteps.STEP_STD_CONSENT_ADD:
            return reverse('study-consent', args=[self.slug])
        elif step == StudySteps.STEP_STD_PUBLISH:
            return reverse('study', args=[self.slug])
        elif step == StudySteps.STEP_STD_FINISH:
            return reverse('study', args=[self.slug])
        elif step == StudySteps.STEP_STD_RESULTS:
            return reverse('trials', args=[self.slug])
        elif step == StudySteps.STEP_STD_ANONYMIZE:
            return reverse('trials', args=[self.slug])
        elif step == StudySteps.STEP_STD_ARCHIVE:
            return reverse('study-settings', args=[self.slug])
        elif step == StudySteps.STEP_STD_OPT_DRAFT:
            return reverse('study', args=[self.slug])
        elif step == StudySteps.STEP_STD_OPT_PUBLISH:
            return reverse('study', args=[self.slug])
        elif step == StudySteps.STEP_STD_OPT_BLOCK_INSTRUCTIONS:
            return reverse('questionnaire-blocks', args=[self.slug])
        elif step == StudySteps.STEP_STD_OPT_SETTINGS:
            return reverse('study-settings', args=[self.slug])
        elif step == StudySteps.STEP_STD_OPT_LABELS:
            return reverse('study-labels', args=[self.slug])
        elif step == StudySteps.STEP_STD_OPT_SHARE:
            return reverse('study-share', args=[self.slug])
        elif step == StudySteps.STEP_STD_OPT_INVOICE:
            return reverse('study-invoice', args=[self.slug])

    def _append_step_info(self, steps, step, group):
        if group not in steps:
            steps.update({group: []})
        steps[group].append((self.STEP_DESCRIPTION[step], self.step_url(step)))

    def next_steps(self):
        next_steps = OrderedDict()

        group = 'Task and instructions'
        if not self.questions.exists():
            self._append_step_info(next_steps, StudySteps.STEP_STD_QUESTION_CREATE, group)
        if not self.instructions:
            self._append_step_info(next_steps, StudySteps.STEP_STD_INSTRUCTIONS_EDIT, group)
        if not self.intro:
            self._append_step_info(next_steps, StudySteps.STEP_STD_INTRO_EDIT, group)

        if not self.materials.exists():
            group = 'Materials'
            self._append_step_info(next_steps, StudySteps.STEP_STD_EXP_CREATE, group)
        else:
            for materials in self.materials.all():
                next_exp_steps = materials.next_steps()
                next_steps.update(next_exp_steps)

        group = 'Questionnaires'
        if self.is_allowed_create_questionnaires and not self.questionnaires.exists():
            self._append_step_info(next_steps, StudySteps.STEP_STD_QUESTIONNAIRES_GENERATE, group)

        group = 'Info and consent'
        if not self.contact_name:
            self._append_step_info(next_steps, StudySteps.STEP_STD_CONTACT_ADD, group)
        if not self.consent_form_text:
            self._append_step_info(next_steps, StudySteps.STEP_STD_CONSENT_ADD, group)

        group = 'Dashboard'
        if self.is_published:
            self._append_step_info(next_steps, StudySteps.STEP_STD_FINISH, group)
        elif not self.is_finished:
            if self.is_allowed_publish:
                self._append_step_info(next_steps, StudySteps.STEP_STD_PUBLISH, group)

        group = 'Results'
        if self.is_finished:
            if self.trial_count_finished > 0:
                self._append_step_info(next_steps, StudySteps.STEP_STD_RESULTS, group)
            if self.has_participant_information:
                self._append_step_info(next_steps, StudySteps.STEP_STD_ANONYMIZE, group)

        group = 'Settings'
        if self.is_finished:
            self._append_step_info(next_steps, StudySteps.STEP_STD_ARCHIVE, group)

        return next_steps

    def optional_steps(self):
        steps = {}
        if self.is_published:
            self._append_step_info(steps, StudySteps.STEP_STD_OPT_DRAFT, 'Dashboard')
        elif self.is_finished:
            self._append_step_info(steps, StudySteps.STEP_STD_OPT_DRAFT, 'Dashboard')
            self._append_step_info(steps, StudySteps.STEP_STD_OPT_PUBLISH, 'Dashboard')
        else:
            if self.use_blocks and self.has_questionnaires and not self.has_block_instructions:
                self._append_step_info(steps, StudySteps.STEP_STD_OPT_BLOCK_INSTRUCTIONS, 'Questionnaires')
            group = 'Settings'
            self._append_step_info(steps, StudySteps.STEP_STD_OPT_SETTINGS, group)
            self._append_step_info(steps, StudySteps.STEP_STD_OPT_LABELS, group)
            self._append_step_info(steps, StudySteps.STEP_STD_OPT_SHARE, group)
        if not self.has_invoice:
            self._append_step_info(steps, StudySteps.STEP_STD_OPT_INVOICE, 'Settings')
        return steps


class Question(models.Model):
    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE,
        related_name='questions',
    )
    number = models.IntegerField(
        default=0,
    )
    question = models.CharField(
        max_length=1000,
        help_text='Question text for this item (e.g. "How acceptable is this sentence?").',
    )
    legend = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
        help_text='Legend to clarify the scale (e.g. "1 = bad, 5 = good").',
    )
    randomize_scale = models.BooleanField(
        default=False,
        help_text='Show scale labels in random order.',
    )
    RATING_COMMENT_NONE = 'none'
    RATING_COMMENT_OPTIONAL = 'optional'
    RATING_COMMENT_REQUIRED = 'required'
    RATING_COMMENT = (
        (RATING_COMMENT_NONE, 'None'),
        (RATING_COMMENT_OPTIONAL, 'Optional'),
        (RATING_COMMENT_REQUIRED, 'Required'),
    )
    rating_comment = models.CharField(
        max_length=10,
        choices=RATING_COMMENT,
        default=RATING_COMMENT_NONE,
        help_text='Let the participant add a comment to the rating (free text).',
    )

    class Meta:
        ordering = ['study', 'number']

    @cached_property
    def has_rating_comment(self):
        return self.rating_comment != self.RATING_COMMENT_NONE

    def get_scale_labels(self, multiline=False):
        labels = [scale_value.label for scale_value in self.scale_values.all()]
        return to_list_string(labels, multiline)

    def is_valid_scale_value(self, scale_value_label):
        return self.scale_values.filter(label=scale_value_label).exists()

    def get_absolute_url(self):
        return reverse('study-question', args=[self.study.slug, self.pk])

    def __str__(self):
        return self.question


class ScaleValue(models.Model):
    number = models.IntegerField(
        default=0,
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='scale_values',
    )
    LABEL_MAX_LENGTH = 1000
    label = models.TextField(
        max_length=LABEL_MAX_LENGTH,
        help_text='Provide a label for this point of the scale.',
    )

    class Meta:
        ordering = ['question', 'number']

    def __str__(self):
        return self.label


class DemographicField(models.Model):
    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE,
        related_name='demographics'
    )
    number = models.IntegerField(
        default=0,
    )
    name = models.CharField(
        max_length=500,
        help_text='You can enter a demographic question (e.g., "age" or "native languages"). The participants will '
                  'have to answer it (free text input) at the beginning of the study.',
        verbose_name='question'
    )

    class Meta:
        ordering = ['study', 'number']

    def __str__(self):
        return self.name
