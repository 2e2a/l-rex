import csv
import io
import re
import zipfile
from collections import OrderedDict
from itertools import groupby
from markdownx.models import MarkdownxField

from enum import Enum
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.timezone import now

from apps.contrib import csv as contrib_csv
from apps.contrib import math
from apps.contrib.utils import slugify_unique
from apps.contrib.datefield import DateField


class StudyStatus(Enum):
    DRAFT = 1
    STARTED = 2
    ACTIVE = 3
    FINISHED = 4
    ARCHIVED = 5


class StudySteps(Enum):
    STEP_STD_QUESTION_CREATE = 1
    STEP_STD_INSTRUCTIONS_EDIT = 2
    STEP_STD_INTRO_EDIT = 3
    STEP_STD_EXP_CREATE = 4
    STEP_STD_QUESTIONNAIRES_GENERATE = 5
    STEP_STD_BLOCK_INSTRUCTIONS_CREATE = 6
    STEP_STD_CONTACT_ADD = 7
    STEP_STD_PRIVACY_ADD = 8
    STEP_STD_PUBLISH = 9
    STEP_STD_UNPUBLISH = 10
    STEP_STD_RESULTS = 11
    STEP_STD_ANONYMIZE = 12
    STEP_STD_ARCHIVE = 13


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
    instructions = MarkdownxField(
        blank=True,
        null=True,
        max_length=5000,
        help_text='These instructions will be presented to the participant before the experiment begins.',
    )
    require_participant_id = models.BooleanField(
        default=False,
        help_text='Enable if you want participants to enter an ID before participation.',
        verbose_name='Participant ID required',
    )
    link_instructions = models.BooleanField(
        default=False,
        help_text='Make a link to the instructions available at any time during participation.',
    )
    link_block_instructions = models.BooleanField(
        default=False,
        help_text='Make the current block instructions available under the instructions link.',
    )
    end_date = DateField(
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
    privacy_statement = MarkdownxField(
        null=True,
        blank=True,
        max_length=5000,
        help_text='This statement will be shown to the participants before the study begins. '
                  'It should state whether the study is fully anonymous or not. '
                  'If you ask for individual IDs or personal data in your study, the privacy '
                  'statement should include the following information: for what purpose '
                  'is the ID/personal data collected, how long will the data be stored in non-anonymized '
                  'form, and who is responsible for data processing?'
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
    privacy_statement_label = models.CharField(
        max_length=40,
        default='Privacy statement',
        help_text='Label for "Privacy statement" used during participation.',
    )
    contact_label = models.CharField(
        max_length=40,
        default='Contact',
        help_text='Label for "Contact" used during participation.',
    )
    instructions_label = models.CharField(
        max_length=40,
        default='Instructions',
        help_text='Label of the "Instructions" link used during participation.',
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
    answer_question_message = models.CharField(
        max_length=500,
        default='Please answer this question.',
        help_text='Error message shown to participant if the question was not answered.',
    )
    answer_questions_message = models.CharField(
        max_length=500,
        default='Please answer all questions.',
        help_text='Error message shown to participant if a question was not answered.',
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
    shared_with = models.CharField(
        null=True,
        blank=True,
        max_length=200,
        help_text='Give other users access to the study. Enter comma-separated user names (e.g. "user1, user2").',
    )
    created_date = DateField(
        default=now,
        editable=False,
    )
    is_archived = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ['-created_date']

    def save(self, *args, **kwargs):
        new_slug = slugify_unique(self.title, Study, self.id)
        if self.slug != new_slug:
            self.slug = new_slug
            for materials in self.materials_list:
                materials.save()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('study', args=[self.slug])

    @cached_property
    def materials_list(self):
        return self.materials_set.all()

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
        item_bocks = set()
        for materials in self.materials_list:
            item_bocks.update(materials.item_blocks)
        return sorted(item_bocks)

    @cached_property
    def questions(self):
        return self.question_set.all()

    @cached_property
    def question(self):
        return self.questions[0] if self.questions else None

    def get_question(self, number):
        for question in self.questions:
            if question.number == number:
                return question

    @cached_property
    def is_multi_question(self):
        return len(self.questions) > 1

    @cached_property
    def has_question_with_random_scale(self):
        return any(question.randomize_scale for question in self.questions)

    @cached_property
    def has_question_rating_comments(self):
        return self.question_set.filter(
            rating_comment__in=[Question.RATING_COMMENT_OPTIONAL, Question.RATING_COMMENT_REQUIRED]
        ).exists()

    @cached_property
    def has_items(self):
        from apps.item.models import Item
        return Item.objects.filter(materials__in=self.materials_list).exists()

    @cached_property
    def has_item_questions(self):
        from apps.item.models import Item, ItemQuestion
        try:
            materials_items = Item.objects.filter(materials__in=self.materials_list).all()
            return ItemQuestion.objects.filter(item__in=materials_items).exists()
        except Item.DoesNotExist:
            return False

    @cached_property
    def has_block_instructions(self):
        if not self.questionnaireblock_set.exists():
            return False
        for block in self.questionnaireblock_set.all():
            if not block.instructions:
                return False
        return True

    @cached_property
    def has_item_lists(self):
        return any(materials.has_lists for materials in self.materials_list)

    @cached_property
    def has_demographics(self):
        return self.demographicfield_set.exists()

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
        map(lambda trial: trial.delete(), trials_abandoned)

    def delete_test_trials(self):
        from apps.trial.models import Trial
        Trial.objects.filter(questionnaire__study=self, is_test=True).delete()

    @property
    def has_subject_mapping(self):
        from apps.trial.models import Trial
        return Trial.objects.filter(questionnaire__study=self).exclude(subject_id=None).exists()

    def delete_subject_mapping(self):
        from apps.trial.models import Trial
        Trial.objects.filter(questionnaire__study=self).update(subject_id=None)

    @cached_property
    def is_rating_possible(self):
        return self.status == StudyStatus.ACTIVE or self.status == StudyStatus.STARTED

    @cached_property
    def is_allowed_create_questionnaires(self):
        if not self.materials_list:
            return False
        for materials in self.materials_list:
            if not materials.is_complete:
                return False
        return True

    @cached_property
    def is_allowed_publish(self):
        return self.questions and self.instructions \
               and self.items_validated and self.questionnaire_set.exists() \
               and (not self.use_blocks or self.has_block_instructions)

    @cached_property
    def is_allowed_pseudo_randomization(self):
        return self.materials_set.filter(is_filler=True).count() > 0

    @cached_property
    def items_validated(self):
        for materials in self.materials_list:
            if not materials.items_validated:
                return False
        return True

    @cached_property
    def randomization_reqiured(self):
        from apps.trial.models import QuestionnaireBlock
        for questionnaire_block in self.questionnaireblock_set.all():
            if questionnaire_block.randomization != QuestionnaireBlock.RANDOMIZATION_NONE:
                return True
        return False

    @cached_property
    def has_exmaples(self):
        return any(materials.is_example for materials in self.materials_list)

    @cached_property
    def has_questionnaires(self):
        return self.questionnaire_set.exists()

    def _questionnaire_trial_count(self, is_test=False):
        from apps.trial.models import Trial
        questionnaires = self.questionnaire_set.all()
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

    def _questionnaire_count(self):
        questionnaire_lcm = 1
        for materials in self.materials_list:
            condition_count = len(materials.conditions)
            questionnaire_lcm = math.lcm(questionnaire_lcm,  condition_count)
        return questionnaire_lcm

    def _init_questionnaire_lists(self):
        questionnaire_item_list = []
        for materials in self.materials_list:
            item_list = materials.itemlist_set.first()
            questionnaire_item_list.append(item_list)
        return questionnaire_item_list

    def _next_questionnaire_lists(self, last_questionnaire):
        questionnaire_item_list = []
        last_item_lists = last_questionnaire.item_lists.all()
        for last_item_list in last_item_lists:
            next_item_list = last_item_list.next()
            questionnaire_item_list.append(next_item_list)
        return questionnaire_item_list

    def _create_next_questionnaire(self, last_questionnaire, num):
        from apps.trial.models import Questionnaire
        questionnaire = Questionnaire.objects.create(study=self, number=num)
        if not last_questionnaire:
            questionnaire_item_lists = self._init_questionnaire_lists()
        else:
            questionnaire_item_lists = self._next_questionnaire_lists(last_questionnaire)
        for item_list in questionnaire_item_lists:
            questionnaire.item_lists.add(item_list)
        return questionnaire

    def _generate_questionnaire_permutations(self, materials_list, permutations=4):
        from apps.trial.models import Questionnaire
        if self.randomization_reqiured:
            questionnaires = list(self.questionnaire_set.all())
            questionnaire_count = len(questionnaires)
            for permutation in range(1, permutations):
                for i, questionnaire in enumerate(questionnaires):
                    num = questionnaire_count * permutation + i + 1
                    questionnaire_permutation=Questionnaire.objects.create(study=self, number=num)
                    questionnaire_permutation.item_lists.set(questionnaire.item_lists.all())
                    questionnaire_permutation.generate_items(materials_list)

    def generate_questionnaires(self):
        try:
            self.questionnaire_set.all().delete()
            materials_list = {e.id: e for e in self.materials_list}
            questionnaire_count = self._questionnaire_count()
            last_questionnaire = None
            for i in range(questionnaire_count):
                last_questionnaire = self._create_next_questionnaire(last_questionnaire, i + 1)
                last_questionnaire.generate_items(materials_list)
            if self.randomization_reqiured:
                self._generate_questionnaire_permutations(materials_list)
        except RuntimeError as error:
            self.delete_questionnaires()
            raise error

    def delete_questionnaires(self):
        from apps.trial.models import Trial
        Trial.objects.filter(questionnaire__study=self).all().delete()
        self.questionnaire_set.all().delete()

    def delete_questionnaire_blocks(self):
        self.questionnaireblock_set.all().delete()

    @cached_property
    def contact_html(self):
        return '<strong>{}</strong>, {}<a href="mailto:{}">{}</a>'.format(
            self.contact_name,
            '{}, '.format(self.contact_affiliation) if self.contact_affiliation else '',
            self.contact_email,
            self.contact_email,
        )

    def subject_mapping_csv(self, fileobj):
        from apps.trial.models import Trial
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        csv_row = [
            'Subject',
            'ID'
        ]
        writer.writerow(csv_row)
        trials = Trial.objects.filter(questionnaire__study=self, is_test=False)
        for i, trial in enumerate(trials, 1):
            csv_row = [i, trial.subject_id]
            writer.writerow(csv_row)

    def settings_csv(self, fileobj):
        # TODO: Add archive version + possibility for migrations
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        writer.writerow(['title', self.title])
        writer.writerow(['item_type', self.item_type])
        writer.writerow(['use_blocks', self.use_blocks])
        writer.writerow(['pseudo_randomize_question_order', self.pseudo_randomize_question_order])
        writer.writerow(['password', self.password])
        writer.writerow(['require_participant_id', self.require_participant_id])
        writer.writerow(['end_date', self.end_date])
        writer.writerow(['trial_limit', self.trial_limit])
        writer.writerow(['questions', ','.join('"{}"'.format(question) for question in self.questions)])
        writer.writerow(['question_scales', ','.join('"{}"'.format(question.scale_labels) for question in self.questions)])
        writer.writerow(['question_legends', ','.join('"{}"'.format(question.legend if question.legend else '') for question in self.questions)])
        writer.writerow(['instructions', self.instructions])
        writer.writerow(['outro', self.outro])
        writer.writerow(['continue_label', self.password])
        writer.writerow(['materials_list', ','.join('"{}"'.format(materials.title) for materials in self.materials_list)])
        writer.writerow(['filler', ','.join('"{}"'.format(materials.title) for materials in self.materials_list if materials.is_filler)])

    def _read_settings(self, reader):
        study_settings = {}
        for row in reader:
            if len(row) >= 2:
                study_settings.update({row[0]: row[1]})
        return study_settings

    SETTING_BOOL_FIELDS = [
        'use_blocks',
        'pseudo_randomize_question_order',
        'require_participant_id',
        'generate_participation_code',
    ]

    SETTING_CHAR_FIELDS = [
        'title',
        'item_type',
        'password',
        'end_date',
        'trial_limit',
        'instructions',
        'outro'
    ]

    def settings_csv_restore(self, fileobj):
        from apps.materials.models import Materials
        reader = csv.reader(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        study_settings = self._read_settings(reader)
        if not self.is_archived:
            for field in self.SETTING_CHAR_FIELDS:
                if field in study_settings and study_settings[field]:
                    setattr(self, field, study_settings[field])
            for field in self.SETTING_BOOL_FIELDS:
                if field in study_settings and study_settings[field]:
                    setattr(self, field, study_settings[field] in ['True', 'true'])
            self.save()
        questions = re.findall('"([^"]+)"', study_settings['questions'])
        scales = re.findall('"([^"]+)"', study_settings['question_scales'])
        legends = re.findall('"([^"]*)"', study_settings['question_legends'])
        for i, (question, scale, legend) in enumerate(zip(questions, scales, legends)):
            question = Question.objects.create(
                study=self,
                question=question,
                legend=legend,
                number=i,
            )
            for i, scale_value in enumerate(scale.split(',')):
                ScaleValue.objects.create(
                    number=i,
                    question=question,
                    label=scale_value,
                )
        materials_titles = re.findall('"([^"]+)"', study_settings['materials_list'])
        materials_fillers = re.findall('"([^"]+)"', study_settings['filler'])
        for materials_title in materials_titles:
            Materials.objects.create(
                study=self,
                title=materials_title,
                is_filler=materials_title in materials_fillers,
            )
        self.created_date = now().date()
        self.is_published = False
        self.is_archived = False
        self.save()

    def results_csv(self, fileobj):
        for i, materials in enumerate(self.materials_list):
            if i == 0:
                writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
                header = materials.results_csv_header()
                writer.writerow(header)
            materials.results_csv(fileobj)

    def items_csv(self, fileobj):
        for i, materials in enumerate(self.materials_list):
            if i == 0:
                writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
                header = materials.items_csv_header(add_materials_column=True)
                writer.writerow(header)
            materials.items_csv(fileobj, add_header=False, add_materials_column=True)

    def items_csv_restore(self, fileobj, **kwargs):
        for materials in self.materials_set.all():
            fileobj.seek(0)
            materials.items_csv_create(fileobj, has_materials_column=True)

    def itemlists_csv(self, fileobj):
        for i, materials in enumerate(self.materials_list):
            if i == 0:
                writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
                header = materials.itemlists_csv_header(add_materials_column=True)
                writer.writerow(header)
            materials.itemlists_csv(fileobj, add_header=False, add_materials_column=True)

    def itemlists_csv_restore(self, fileobj, **kwargs):
        for materials in self.materials_set.all():
            fileobj.seek(0)
            materials.itemlists_csv_create(fileobj, has_materials_column=True)

    def _csv_columns(self, header_func, user_columns=None):
        columns = {}
        header = header_func()
        for i, column in enumerate(header):
            column_num = i
            if user_columns and column in user_columns:
                column_num = int(user_columns[column])
            if column_num >= 0:
                columns.update({column: column_num})
        return columns

    def questionnaires_csv_header(self):
        return ['questionnaire', 'lists', 'items', 'question_order']

    def questionnaires_csv(self, fileobj):
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        header = self.questionnaires_csv_header()
        writer.writerow(header)
        for questionnaire in self.questionnaire_set.all():
            csv_row = [
                questionnaire.number,
                ','.join(['{}-{}'.format(item_list.materials.title, item_list.number)
                          for item_list in questionnaire.item_lists.all()]),
                ','.join(['{}-{}'.format(item.materials.title, item) for item in questionnaire.items]),
            ]
            if self.pseudo_randomize_question_order:
                csv_row.append(
                    ','.join('"{}"'.format(q_item.question_order) for q_item in questionnaire.questionnaire_items)
                )
            else:
                csv_row.append('')
            writer.writerow(csv_row)

    def questionnaires_csv_restore(self, fileobj, user_columns=None, detected_csv=contrib_csv.DEFAULT_DIALECT):
        from apps.trial.models import Questionnaire, QuestionnaireItem
        from apps.trial.forms import QuestionnaireUploadForm
        self.delete_questionnaires()
        reader = csv.reader(fileobj, delimiter=detected_csv['delimiter'], quoting=detected_csv['quoting'])
        if detected_csv['has_header']:
            next(reader)
        columns = self._csv_columns(self.questionnaires_csv_header, user_columns=user_columns)
        for row in reader:
            if not row:
                continue
            questionnaire = Questionnaire.objects.create(study=self, number=row[columns['questionnaire']])
            if 'lists' in columns:
                item_lists = QuestionnaireUploadForm.read_item_lists(self, row[columns['lists']])
                questionnaire.item_lists.set(item_lists)
            items = QuestionnaireUploadForm.read_items(self, row[columns['items']])
            if self.pseudo_randomize_question_order:
                question_orders = re.findall('"([^"]+)"', row[columns['question_order']])
            for i, item in enumerate(items):
                QuestionnaireItem.objects.create(
                    number=i,
                    questionnaire=questionnaire,
                    item=item,
                    question_order=question_orders[i] if self.pseudo_randomize_question_order else None,
                )
            questionnaire.save()

    def questionnaire_blocks_csv_header(self):
        return ['block', 'randomization', 'instructions']

    def questionnaire_blocks_csv(self, fileobj):
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        header = self.questionnaire_blocks_csv_header()
        writer.writerow(header)
        if not self.use_blocks:
            return
        for block in self.questionnaireblock_set.all():
            csv_row = [
                block.block,
                block.randomization,
                block.instructions
            ]
            writer.writerow(csv_row)

    def questionnaire_blocks_csv_restore(self, fileobj, user_columns=None, detected_csv=contrib_csv.DEFAULT_DIALECT):
        from apps.trial.models import QuestionnaireBlock
        self.delete_questionnaire_blocks()
        if not self.use_blocks:
            return
        reader = csv.reader(fileobj, delimiter=detected_csv['delimiter'], quoting=detected_csv['quoting'])
        if detected_csv['has_header']:
            next(reader)
        columns = self._csv_columns(self.questionnaire_blocks_csv_header, user_columns=user_columns)
        for row in reader:
            if not row:
                continue
            QuestionnaireBlock.objects.create(
                study=self,
                block=row[columns['block']],
                instructions=row[columns['instructions']],
                randomization=row[columns['randomization']] if 'randomization' in columns else None,
            )

    @property
    def ARCHIVE_FILES(self):
        return [
            ('01_results.csv', self.results_csv, None),
            ('02_settings.csv', self.settings_csv, self.settings_csv_restore),
            ('03_items.csv', self.items_csv, self.items_csv_restore),
            ('04_lists.csv', self.itemlists_csv, self.itemlists_csv_restore),
            ('05_questionnaires.csv', self.questionnaires_csv, self.questionnaires_csv_restore),
            ('06_blocks.csv', self.questionnaire_blocks_csv, self.questionnaire_blocks_csv_restore)
        ]

    def archive_file(self, fileobj):
        with zipfile.ZipFile(fileobj, 'w', zipfile.ZIP_DEFLATED) as archive:
            file = io.StringIO()
            for archive_file, archive_func, _ in self.ARCHIVE_FILES:
                if archive_func:
                    file.truncate(0)
                    file.seek(0)
                    archive_func(file)
                    archive.writestr(archive_file, file.getvalue())

    def archive(self):
        self.delete_questionnaires()
        for materials in self.materials_list:
            materials.delete()
        for question in self.questions:
            question.delete()
        self.is_archived = True
        self.save()

    def restore_from_archive(self, fileiobj, detected_csv_dialect=None):
        with zipfile.ZipFile(fileiobj) as archive:
            for archive_file, _, restore_func  in self.ARCHIVE_FILES:
                if restore_func:
                    try:
                        with archive.open(archive_file) as file:
                            text_file = io.TextIOWrapper(file)
                            restore_func(text_file)
                    except KeyError:
                        pass

    @classmethod
    def create_from_archive_file(cls, fileobj, creator, detected_csv_dialect=None):
        study = cls()
        study.creator = creator
        study.restore_from_archive(fileobj, detected_csv_dialect=detected_csv_dialect)
        return study

    STEP_DESCRIPTION = {
        StudySteps.STEP_STD_QUESTION_CREATE: 'create a question',
        StudySteps.STEP_STD_INSTRUCTIONS_EDIT: 'create instructions',
        StudySteps.STEP_STD_INTRO_EDIT: 'create intro/outro',
        StudySteps.STEP_STD_EXP_CREATE: 'create materials',
        StudySteps.STEP_STD_QUESTIONNAIRES_GENERATE: 'generate questionnaires',
        StudySteps.STEP_STD_BLOCK_INSTRUCTIONS_CREATE: 'define instructions for questionnaire blocks',
        StudySteps.STEP_STD_CONTACT_ADD: 'add contact information',
        StudySteps.STEP_STD_PRIVACY_ADD: 'add a privacy statement',
        StudySteps.STEP_STD_PUBLISH: 'publish the study',
        StudySteps.STEP_STD_UNPUBLISH: 'unpublish the study when finished',
        StudySteps.STEP_STD_RESULTS: 'download results',
        StudySteps.STEP_STD_ANONYMIZE: 'remove subject mapping',
        StudySteps.STEP_STD_ARCHIVE: 'archive the study',
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
        elif step == StudySteps.STEP_STD_BLOCK_INSTRUCTIONS_CREATE:
            return reverse('questionnaire-blocks', args=[self.slug])
        elif step == StudySteps.STEP_STD_CONTACT_ADD:
            return reverse('study-contact', args=[self.slug])
        elif step == StudySteps.STEP_STD_PRIVACY_ADD:
            return reverse('study-privacy', args=[self.slug])
        elif step == StudySteps.STEP_STD_PUBLISH:
            return reverse('study', args=[self.slug])
        elif step == StudySteps.STEP_STD_UNPUBLISH:
            return reverse('study', args=[self.slug])
        elif step == StudySteps.STEP_STD_RESULTS:
            return reverse('trials', args=[self.slug])
        elif step == StudySteps.STEP_STD_ANONYMIZE:
            return reverse('trials', args=[self.slug])
        elif step == StudySteps.STEP_STD_ARCHIVE:
            return reverse('study', args=[self.slug])

    def _append_step_info(self, steps, step, group):
        if group not in steps:
            steps.update({group: []})
        steps[group].append((self.STEP_DESCRIPTION[step], self.step_url(step)))

    def next_steps(self):
        next_steps = OrderedDict()

        group = 'Task and instructions'
        if not self.questions:
            self._append_step_info(next_steps, StudySteps.STEP_STD_QUESTION_CREATE, group)
        if not self.instructions:
            self._append_step_info(next_steps, StudySteps.STEP_STD_INSTRUCTIONS_EDIT, group)
        if not self.intro:
            self._append_step_info(next_steps, StudySteps.STEP_STD_INTRO_EDIT, group)

        if not self.materials_list:
            group = 'Materials'
            self._append_step_info(next_steps, StudySteps.STEP_STD_EXP_CREATE, group)
        else:
            for materials in self.materials_list:
                next_exp_steps = materials.next_steps()
                next_steps.update(next_exp_steps)

        group = 'Questionnaires'
        if self.is_allowed_create_questionnaires and not self.questionnaire_set.exists():
            self._append_step_info(next_steps, StudySteps.STEP_STD_QUESTIONNAIRES_GENERATE, group)
        if self.use_blocks and self.has_questionnaires and not self.has_block_instructions:
            self._append_step_info(next_steps, StudySteps.STEP_STD_BLOCK_INSTRUCTIONS_CREATE, group)

        group = 'Contact and privacy'
        if not self.contact_name:
            self._append_step_info(next_steps, StudySteps.STEP_STD_CONTACT_ADD, group)
        if not self.privacy_statement:
            self._append_step_info(next_steps, StudySteps.STEP_STD_PRIVACY_ADD, group)

        group = 'Study'
        if self.is_published:
            self._append_step_info(next_steps, StudySteps.STEP_STD_UNPUBLISH, group)
        else:
            if self.is_allowed_publish:
                self._append_step_info(next_steps, StudySteps.STEP_STD_PUBLISH, group)
        if self.trial_count_finished > 0:
            self._append_step_info(next_steps, StudySteps.STEP_STD_RESULTS, group)
        if self.has_subject_mapping:
            self._append_step_info(next_steps, StudySteps.STEP_STD_ANONYMIZE, group)

        # TODO: add archive
        return next_steps

    def optional_steps(self):
        if self.is_published:
            return {}
        return {
            'Settings':
                [
                    ('customize study settings', reverse('study-settings', args=[self.slug])),
                    ('translate build-in texts', reverse('study-translate', args=[self.slug])),
                ]
        }

class Question(models.Model):
    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE
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
    def scale_values(self):
        return list(self.scalevalue_set.all())

    @cached_property
    def scale_labels(self):
        return ','.join([scale_value.label for scale_value in self.scalevalue_set.all()])

    @cached_property
    def has_rating_comment(self):
        return self.rating_comment != self.RATING_COMMENT_NONE

    def is_valid_scale_value(self, scale_value_label):
        return any(scale_value.label == scale_value_label for scale_value in self.scalevalue_set.all())

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
        on_delete=models.CASCADE
    )
    label = models.CharField(
        max_length=50,
        help_text='Provide a label for this point of the scale.',
    )

    class Meta:
        ordering = ['question', 'number']

    def __str__(self):
        return self.label


class DemographicField(models.Model):
    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=500,
        help_text='You can enter a demographic question (e.g., "age" or "native languages"). The participants will '
                  'have to answer it (free text input) at the beginning of the study.',
        verbose_name='question'
    )

    class Meta:
        ordering = ['study', 'pk']

    def __str__(self):
        return self.name
