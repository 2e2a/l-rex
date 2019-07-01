import csv
import io
import re
import zipfile
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
    STEP_STD_EXP_CREATE = 3
    STEP_STD_QUESTIONNAIRES_GENERATE = 4
    STEP_STD_BLOCK_INSTRUCTIONS_CREATE = 5
    STEP_STD_PUBLISH = 6


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
        (ITEM_TYPE_AUDIO_LINK, 'Audio link'),
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
                  'instructions',
    )
    pseudo_randomize_question_order = models.BooleanField(
        default=False,
        help_text='Show questions in a random order, if multiple questions defined.',
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
        help_text='Enable if you want participants to enter some ID before participation.',
        verbose_name='Participant ID required',
    )
    generate_participation_code = models.BooleanField(
        default=False,
        help_text='Generate a proof code for the subject participation.',
    )
    outro = MarkdownxField(
        blank=True,
        null=True,
        max_length=5000,
        help_text='This text will be presented to the participant after the experiment is finished.',
    )
    continue_label = models.CharField(
        max_length=40,
        default='Continue',
        help_text='Label of the "Continue" button used during participation.',
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
    is_published = models.BooleanField(
        default=False,
        help_text='Enable to publish your study. It will then be available for participation.',
    )
    shared_with = models.CharField(
        null=True,
        blank=True,
        max_length=200,
        help_text='Give other users access to the study, enter comma separated user names.',
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
            for experiment in self.experiments:
                experiment.save()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('study', args=[self.slug])

    @cached_property
    def experiments(self):
        return self.experiment_set.all()

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
        for experiment in self.experiments:
            item_bocks.update(experiment.item_blocks)
        return sorted(item_bocks)

    @cached_property
    def questions(self):
        return self.question_set.all()

    @cached_property
    def question(self):
        return self.questions[0] if self.questions else None

    @cached_property
    def is_multi_question(self):
        return len(self.questions) > 1

    @cached_property
    def has_items(self):
        from apps.item.models import Item
        return Item.objects.filter(experiment__in=self.experiments).exists()

    @cached_property
    def has_item_questions(self):
        from apps.item.models import Item, ItemQuestion
        try:
            experiment_items = Item.objects.filter(experiment__in=self.experiments).all()
            return ItemQuestion.objects.filter(item__in=experiment_items).exists()
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

    @property
    def status(self):
        if self.is_archived:
            return StudyStatus.ARCHIVED
        if not self.is_published:
            return StudyStatus.DRAFT
        if self.end_date and self.end_date < timezone.now().date():
            return StudyStatus.FINISHED
        if self.trial_limit  and self.trial_limit <= self.trial_count:
            return StudyStatus.FINISHED
        if self.trial_count > 0:
            return StudyStatus.ACTIVE
        return StudyStatus.STARTED

    @cached_property
    def is_active(self):
        return self.is_published or self.trial_count > 0

    @cached_property
    def trial_count(self):
        from apps.trial.models import Trial
        return Trial.objects.filter(questionnaire__study=self, is_test=False).count()

    @cached_property
    def trial_count_test(self):
        from apps.trial.models import Trial
        return Trial.objects.filter(questionnaire__study=self, is_test=True).count()

    @cached_property
    def trial_count_active(self):
        from apps.trial.models import Trial, TrialStatus
        trials = Trial.objects.filter(questionnaire__study=self, is_test=False)
        return len([trial for trial in trials if trial.status in [TrialStatus.CREATED, TrialStatus.STARTED]])

    @cached_property
    def trial_count_finished(self):
        from apps.trial.models import Trial, TrialStatus
        trials = Trial.objects.filter(questionnaire__study=self, is_test=False)
        return len([trial for trial in trials if trial.status == TrialStatus.FINISHED])

    @cached_property
    def trial_count_abandoned(self):
        from apps.trial.models import Trial, TrialStatus
        trials = Trial.objects.filter(questionnaire__study=self, is_test=False)
        return len([trial for trial in trials if trial.status == TrialStatus.ABANDONED])

    @cached_property
    def is_rating_possible(self):
        return self.status == StudyStatus.ACTIVE or self.status == StudyStatus.STARTED

    @cached_property
    def results_url(self):
        if self.experiment_set.count() == 1:
            experiment = self.experiment_set.first()
            return reverse('experiment-results', args=[experiment.slug])
        return reverse('experiment-result-list', args=[self.slug])

    @cached_property
    def is_allowed_create_questionnaires(self):
        if not self.experiments:
            return False
        for experiment in self.experiments:
            if not experiment.is_complete:
                return False
        return True

    @cached_property
    def is_allowed_publish(self):
        return self.questions and self.instructions \
               and self.items_validated and self.questionnaire_set.exists() \
               and (not self.use_blocks or self.has_block_instructions)

    @cached_property
    def is_allowed_pseudo_randomization(self):
        return self.experiment_set.filter(is_filler=True).count() > 0

    @cached_property
    def items_validated(self):
        for experiment in self.experiments:
            if not experiment.items_validated:
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
        for experiment in self.experiments:
            condition_count = len(experiment.conditions)
            questionnaire_lcm = math.lcm(questionnaire_lcm,  condition_count)
        return questionnaire_lcm

    def _init_questionnaire_lists(self):
        questionnaire_item_list = []
        for experiment in self.experiments:
            item_list = experiment.itemlist_set.first()
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

    def _generate_questionnaire_permutations(self, experiments, permutations=4):
        from apps.trial.models import Questionnaire
        if self.randomization_reqiured:
            questionnaires = list(self.questionnaire_set.all())
            questionnaire_count = len(questionnaires)
            for permutation in range(1, permutations):
                for i, questionnaire in enumerate(questionnaires):
                    num = questionnaire_count * permutation + i + 1
                    questionnaire_permutation=Questionnaire.objects.create(study=self, number=num)
                    questionnaire_permutation.item_lists.set(questionnaire.item_lists.all())
                    questionnaire_permutation.generate_items(experiments)

    def generate_questionnaires(self):
        self.questionnaire_set.all().delete()
        experiments = {e.id: e for e in self.experiments}
        questionnaire_count = self._questionnaire_count()
        last_questionnaire = None
        for i in range(questionnaire_count):
            last_questionnaire = self._create_next_questionnaire(last_questionnaire, i + 1)
            last_questionnaire.generate_items(experiments)
        if self.randomization_reqiured:
            self._generate_questionnaire_permutations(experiments)

    def delete_questionnaires(self):
        from apps.trial.models import Trial
        Trial.objects.filter(questionnaire__study=self).all().delete()
        self.questionnaire_set.all().delete()

    def delete_questionnaire_blocks(self):
        self.questionnaireblock_set.all().delete()

    def rating_proofs_csv(self, fileobj):
        from apps.trial.models import Trial
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        csv_row = [
            'Subject',
            'Proof code'
        ]
        writer.writerow(csv_row)
        trials = Trial.objects.filter(
            questionnaire__study=self
        )
        for trial in trials:
            csv_row = [
                trial.subject_id,
                trial.rating_proof
            ]
            writer.writerow(csv_row)

    def settings_csv(self, fileobj):
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        writer.writerow(['title', self.title])
        writer.writerow(['item_type', self.item_type])
        writer.writerow(['use_blocks', self.use_blocks])
        writer.writerow(['pseudo_randomize_question_order', self.pseudo_randomize_question_order])
        writer.writerow(['password', self.password])
        writer.writerow(['require_participant_id', self.require_participant_id])
        writer.writerow(['generate_participation_code', self.generate_participation_code])
        writer.writerow(['end_date', self.end_date])
        writer.writerow(['trial_limit', self.trial_limit])
        writer.writerow(['questions', ','.join('"{}"'.format(question) for question in self.questions)])
        writer.writerow(['question_scales', ','.join('"{}"'.format(question.scale_labels) for question in self.questions)])
        writer.writerow(['question_legends', ','.join('"{}"'.format(question.legend if question.legend else '') for question in self.questions)])
        writer.writerow(['instructions', self.instructions])
        writer.writerow(['outro', self.outro])
        writer.writerow(['continue_label', self.password])
        writer.writerow(['experiments', ','.join('"{}"'.format(experiment.title) for experiment in self.experiments)])
        writer.writerow(['filler', ','.join('"{}"'.format(experiment.title) for experiment in self.experiments if experiment.is_filler)])

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
        from apps.experiment.models import Experiment
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
        experiment_titles = re.findall('"([^"]+)"', study_settings['experiments'])
        experiment_fillers = re.findall('"([^"]+)"', study_settings['filler'])
        for experiment_title in experiment_titles:
            Experiment.objects.create(
                study=self,
                title=experiment_title,
                is_filler=experiment_title in experiment_fillers,
            )
        self.created_date = now().date()
        self.is_published = False
        self.is_archived = False
        self.save()

    def results_csv(self, fileobj):
        for i, experiment in enumerate(self.experiments):
            if i == 0:
                writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
                header = experiment.results_csv_header(add_experiment_column=True)
                writer.writerow(header)
            experiment.results_csv(fileobj, add_header=False, add_experiment_column=True)

    def items_csv(self, fileobj):
        for i, experiment in enumerate(self.experiments):
            if i == 0:
                writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
                header = experiment.items_csv_header(add_experiment_column=True)
                writer.writerow(header)
            experiment.items_csv(fileobj, add_header=False, add_experiment_column=True)

    def items_csv_restore(self, fileobj, **kwargs):
        for experiment in self.experiment_set.all():
            fileobj.seek(0)
            experiment.items_csv_create(fileobj, has_experiment_column=True)

    def itemlists_csv(self, fileobj):
        for i, experiment in enumerate(self.experiments):
            if i == 0:
                writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
                header = experiment.itemlists_csv_header(add_experiment_column=True)
                writer.writerow(header)
            experiment.itemlists_csv(fileobj, add_header=False, add_experiment_column=True)

    def itemlists_csv_restore(self, fileobj, **kwargs):
        for experiment in self.experiment_set.all():
            fileobj.seek(0)
            experiment.itemlists_csv_create(fileobj, has_experiment_column=True)

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
                ','.join(['{}-{}'.format(item_list.experiment.title, item_list.number)
                          for item_list in questionnaire.item_lists.all()]),
                ','.join(['{}-{}'.format(item.experiment.title, item) for item in questionnaire.items]),
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
        for experiment in self.experiments:
            experiment.delete()
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
        StudySteps.STEP_STD_QUESTION_CREATE: 'Create a question',
        StudySteps.STEP_STD_INSTRUCTIONS_EDIT: 'Create the instructions',
        StudySteps.STEP_STD_EXP_CREATE: 'Create an experiment',
        StudySteps.STEP_STD_QUESTIONNAIRES_GENERATE: 'Generate questionnaires',
        StudySteps.STEP_STD_BLOCK_INSTRUCTIONS_CREATE: 'Define questionnaire block instructions',
        StudySteps.STEP_STD_PUBLISH: 'Publish the study',
    }

    def step_url(self, step):
        if step == StudySteps.STEP_STD_QUESTION_CREATE:
            return reverse('study-questions', args=[self.slug])
        elif step == StudySteps.STEP_STD_INSTRUCTIONS_EDIT:
            return reverse('study-instructions', args=[self.slug])
        elif step == StudySteps.STEP_STD_EXP_CREATE:
            return reverse('experiment-create', args=[self.slug])
        elif step == StudySteps.STEP_STD_QUESTIONNAIRES_GENERATE:
            return reverse('questionnaires', args=[self.slug])
        elif step == StudySteps.STEP_STD_BLOCK_INSTRUCTIONS_CREATE:
            return reverse('questionnaire-blocks', args=[self.slug])
        elif step == StudySteps.STEP_STD_PUBLISH:
            return reverse('study', args=[self.slug])

    def _append_step_info(self, steps, step):
        steps.append((self.STEP_DESCRIPTION[step], self.step_url(step)))

    def next_steps(self):
        next_steps = []
        if not self.questions:
            self._append_step_info(next_steps, StudySteps.STEP_STD_QUESTION_CREATE)
        if not self.instructions:
            self._append_step_info(next_steps, StudySteps.STEP_STD_INSTRUCTIONS_EDIT)
        if not self.experiments:
            self._append_step_info(next_steps, StudySteps.STEP_STD_EXP_CREATE)
        if self.is_allowed_create_questionnaires and not self.questionnaire_set.exists():
            self._append_step_info(next_steps, StudySteps.STEP_STD_QUESTIONNAIRES_GENERATE)
        if self.use_blocks and self.has_questionnaires and not self.has_block_instructions:
            self._append_step_info(next_steps, StudySteps.STEP_STD_BLOCK_INSTRUCTIONS_CREATE)
        if self.is_allowed_publish and not self.is_published:
            self._append_step_info(next_steps, StudySteps.STEP_STD_PUBLISH)
        for experiment in self.experiments:
            next_exp_steps = experiment.next_steps()
            next_steps.extend(next_exp_steps)
        return next_steps


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
        help_text='Question text for this item (e.g. "How acceptable is this sentence?")',
    )
    legend = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
        help_text='Legend to clarify the scale (e.g. "1 = bad, 5 = good")',
    )

    class Meta:
        ordering = ['study', 'number']

    @property
    def scale_labels(self):
        return ','.join([scale_value.label for scale_value in self.scalevalue_set.all()])

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
