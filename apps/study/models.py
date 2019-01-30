import csv
from itertools import groupby

from enum import Enum
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from apps.contrib import math
from apps.contrib.utils import slugify_unique
from apps.contrib.datefield import DateField


class StudyStatus(Enum):
    DRAFT = 1
    STARTED = 2
    ACTIVE = 3
    FINISHED = 4


class Study(models.Model):
    title = models.CharField(
        max_length=200,
        help_text='Give your study a name.',
        )
    slug = models.SlugField(unique=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ITEM_TYPE_TXT = 'txt'
    ITEM_TYPE_AUDIO_LINK = 'aul'
    ITEM_TYPE = (
        (ITEM_TYPE_TXT, 'Text'),
        (ITEM_TYPE_AUDIO_LINK, 'Audio Link'),
    )
    item_type = models.CharField(
        max_length=3,
        choices=ITEM_TYPE,
        default=ITEM_TYPE_TXT,
        help_text='The items can be plain text or links to audio files (self-hosted).',
    )
    password = models.CharField(
        max_length=200,
        help_text='This password will be required to participate in the study.',
    )
    instructions = models.TextField(
        max_length=5000,
        help_text='These instructions will be presented to the participant before the experiment begins.',
        default='Please rate the following sentences on the scale.',
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
    outro = models.TextField(
        max_length=5000,
        help_text='This text will be presented to the participant after the experiment is finished.',
        default='Thank you for participating!',
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

    PROGRESS_STD_CREATED = '00-std-crt'
    PROGRESS_STD_QUESTION_CREATED = '10-qst-crt'
    PROGRESS_STD_INSTRUCTIONS_EDITED = '11-ins-edt'
    PROGRESS_STD_EXP_CREATED = '20-exp-crt'
    PROGRESS_STD_EXP_COMPLETED = '29-exp-cmp'
    PROGRESS_STD_QUESTIONNARES_GENERATED = '30-std-qnr-gen'
    PROGRESS_STD_PUBLISHED = '40-std-pub'
    PROGRESS = (
        (PROGRESS_STD_CREATED, 'Create a study'),
        (PROGRESS_STD_QUESTION_CREATED, 'Create a question'),
        (PROGRESS_STD_INSTRUCTIONS_EDITED, 'Edit the instuctions'),
        (PROGRESS_STD_EXP_CREATED, 'Create an experiment'),
        (PROGRESS_STD_EXP_COMPLETED, 'Complete the experiment creation'),
        (PROGRESS_STD_QUESTIONNARES_GENERATED, 'Generate questionnaires'),
        (PROGRESS_STD_PUBLISHED, 'Publish the study'),
    )
    progress = models.CharField(
        max_length=16,
        choices=PROGRESS,
        default=PROGRESS_STD_CREATED,
    )

    class Meta:
        ordering = ['-pk']

    def save(self, *args, **kwargs):
        new_slug = slugify_unique(self.title, Study, self.id)
        if self.slug != new_slug:
            self.slug = slugify_unique(self.title, Study, self.id)
            for experiment in self.experiments:
                experiment.save()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('study', args=[self.slug])

    @cached_property
    def experiments(self):
        return self.experiment_set.all()

    @cached_property
    def has_text_items(self):
        return self.item_type == self.ITEM_TYPE_TXT

    @cached_property
    def has_audiolink_items(self):
        return self.item_type == self.ITEM_TYPE_AUDIO_LINK

    @cached_property
    def item_blocks(self):
        item_bocks = set()
        for experiment in self.experiments:
            for item in experiment.item_set.all():
                item_bocks.add(item.block)
        return sorted(item_bocks)

    @cached_property
    def questions(self):
        return self.question_set.all()

    @property
    def status(self):
        from apps.trial.models import Trial
        if not self.is_published:
            return StudyStatus.DRAFT
        if self.end_date and self.end_date < timezone.now().date():
            return StudyStatus.FINISHED
        trial_count = Trial.objects.filter(questionnaire__study=self).count()
        if self.trial_limit  and self.trial_limit <= trial_count:
            return StudyStatus.FINISHED
        if trial_count > 0:
            return StudyStatus.ACTIVE
        return StudyStatus.STARTED

    @property
    def is_rating_possible(self):
        return self.status == StudyStatus.ACTIVE or self.status == StudyStatus.STARTED

    @cached_property
    def results_url(self):
        if self.experiment_set.count() == 1:
            experiment = self.experiment_set.first()
            return reverse('experiment-results', args=[experiment.slug])
        return reverse('experiment-result-list', args=[self.slug])

    @cached_property
    def allow_pseudo_randomization(self):
        return self.experiment_set.filter(is_filler=True).count() > 0

    @cached_property
    def randomization_reqiured(self):
        from apps.trial.models import QuestionnaireBlock
        for questionnaire_block in self.questionnaireblock_set.all():
            if questionnaire_block.randomization != QuestionnaireBlock.RANDOMIZATION_NONE:
                return True
        return False

    @property
    def questionnaire_trial_count(self):
        from apps.trial.models import Trial
        questionnaires = self.questionnaire_set.all()
        trials = Trial.objects.filter(
            questionnaire_id__in=[questionnaire.id for questionnaire in questionnaires]
        ).order_by('questionnaire_id')
        trials_per_questionnaire = groupby(trials, lambda x: x.questionnaire_id)
        trial_count_by_id = {q_id: len(list(q_trials)) for q_id, q_trials in trials_per_questionnaire}
        trial_count = {}
        for questionnaire in questionnaires:
            trial_count.update({questionnaire: trial_count_by_id.get(questionnaire.id, 0)})
        return trial_count

    @property
    def next_questionnaire(self):
        trial_count = self.questionnaire_trial_count
        next_questionnaire = min(trial_count, key=trial_count.get)
        return next_questionnaire

    def _questionnaire_count(self):
        questionnaire_lcm = 1
        for experiment in self.experiment_set.all():
            condition_count = len(experiment.conditions)
            questionnaire_lcm = math.lcm(questionnaire_lcm,  condition_count)
        return questionnaire_lcm

    def _init_questionnaire_lists(self):
        questionnaire_item_list = []
        for experiment in self.experiment_set.all():
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

    def rating_proofs_csv(self, fileobj):
        from apps.trial.models import Trial
        writer = csv.writer(fileobj)
        csv_row = [
            'Subject',
            'Proof code'
        ]
        writer.writerow(csv_row)
        trials = Trial.objects.filter(
            questionnaire__study=self
        )
        for i, trial in enumerate(trials):
            csv_row = [
                trial.subject_id if trial.subject_id else i,
                trial.rating_proof
            ]
            writer.writerow(csv_row)

    def progress_reached(self, progress):
        return self.progress >= progress

    @staticmethod
    def progress_description(progress):
        progress_dict = dict(Study.PROGRESS)
        if progress in progress_dict:
            return progress_dict[progress]
        else:
            from apps.experiment.models import Experiment
            return Experiment.progress_description(progress)

    def progress_url(self, progress):
        if progress == self.PROGRESS_STD_CREATED:
            return reverse('study-create', args=[])
        elif progress == self.PROGRESS_STD_QUESTION_CREATED:
            return reverse('study-questions', args=[self])
        elif progress == self.PROGRESS_STD_INSTRUCTIONS_EDITED:
            return reverse('study-instructions', args=[self])
        elif progress == self.PROGRESS_STD_EXP_CREATED:
            return reverse('experiments', args=[self])
        elif progress == self.PROGRESS_STD_EXP_COMPLETED:
            return reverse('study', args=[self])
        elif progress == self.PROGRESS_STD_QUESTIONNARES_GENERATED:
            return reverse('questionnaires', args=[self])
        elif progress == self.PROGRESS_STD_PUBLISHED:
            return reverse('study', args=[self])
        return None

    def set_progress(self, progress):
        change_progress = True
        if progress == self.PROGRESS_STD_EXP_COMPLETED:
            for experiment in self.experiments:
                if experiment.progress != experiment.PROGRESS_EXP_LISTS_CREATED:
                    change_progress = False
        if progress < self.progress:
            if progress == self.PROGRESS_STD_QUESTION_CREATED or progress == self.PROGRESS_STD_QUESTIONNARES_GENERATED:
                change_progress = False
        if change_progress:
            if progress < self.PROGRESS_STD_PUBLISHED:
                self.is_published = False
            self.progress = progress
            self.save()

    def next_progress_steps(self, progress):
        if progress == self.PROGRESS_STD_CREATED:
            return [ self.PROGRESS_STD_QUESTION_CREATED]
        elif progress == self.PROGRESS_STD_QUESTION_CREATED:
            return [ self.PROGRESS_STD_INSTRUCTIONS_EDITED, self.PROGRESS_STD_EXP_CREATED ]
        elif progress == self.PROGRESS_STD_INSTRUCTIONS_EDITED:
            return [ self.PROGRESS_STD_EXP_CREATED ]
        elif progress == self.PROGRESS_STD_EXP_CREATED:
            return [ self.PROGRESS_STD_EXP_COMPLETED ]
        elif progress == self.PROGRESS_STD_EXP_COMPLETED:
            return [ self.PROGRESS_STD_EXP_CREATED, self.PROGRESS_STD_QUESTIONNARES_GENERATED ]
        elif progress == self.PROGRESS_STD_QUESTIONNARES_GENERATED:
            return [ self.PROGRESS_STD_PUBLISHED ]
        elif progress == self.PROGRESS_STD_PUBLISHED:
            return []

    def next_steps(self):
        next_steps = []
        if not next_steps:
            if self.progress == self.PROGRESS_STD_EXP_CREATED:
                for experiment in self.experiments:
                    next_exp_steps = experiment.next_steps()
                    next_steps.extend(next_exp_steps)

        if not next_steps:
            for next_step in self.next_progress_steps(self.progress):
                description = self.progress_description(next_step)
                url = self.progress_url(next_step)
                next_steps.append(( description, url, ))
        return next_steps


class Question(models.Model):
    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE
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
        ordering = ['pk']

    @cached_property
    def num(self):
        return list(Question.objects.filter(study=self.study)).index(self) + 1

    def get_absolute_url(self):
        return reverse('study-question', args=[self.study.slug, self.pk])

    def __str__(self):
        return self.question


class ScaleValue(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    label = models.CharField(
        max_length=50,
        help_text='Provide a label for this point of the scale.',
    )

    class Meta:
        ordering = ['pk']

    @cached_property
    def num(self):
        return list(ScaleValue.objects.filter(question=self.question)).index(self) + 1

    def __str__(self):
        return self.label
