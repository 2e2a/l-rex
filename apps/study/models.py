import csv

from enum import Enum
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone

from apps.contrib import math


class StudyStatus(Enum):
    DRAFT = 1
    ACTIVE = 2
    FINISHED = 3


class Study(models.Model):
    title = models.CharField(
        max_length=200,
        help_text='Give your study a name.',
        unique=True,
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

    rating_instructions = models.TextField(
        max_length=1024,
        help_text='These instructions will be presented to the participant before the experiment begins.',
    )
    password = models.CharField(
        max_length=200,
        help_text='This password will be required to participate in the study.',
    )
    require_participant_id = models.BooleanField(
        default=False,
        help_text='Enable if you want participants to enter some ID before participation.',
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        help_text='If you want to set a participation deadline, enter a date in the format YYYY-MM-DD.',
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

    PROGRESS_STD_CREATED = '00sc'
    PROGRESS_STD_SCALE_CONFIGURED = '01ss'
    PROGRESS_STD_EXP_CREATED = '02se'
    PROGRESS_STD_EXP_COMPLETED = '10ec'
    PROGRESS_STD_QUESTIONNARES_GENERATED = '11sq'
    PROGRESS_STD_PUBLISHED = '20sp'
    PROGRESS = (
        (PROGRESS_STD_CREATED, 'Create a study'),
        (PROGRESS_STD_SCALE_CONFIGURED, 'Configure the rating scale'),
        (PROGRESS_STD_EXP_CREATED, 'Create an experiment'),
        (PROGRESS_STD_EXP_COMPLETED, 'Complete the experiment creation'),
        (PROGRESS_STD_QUESTIONNARES_GENERATED, 'Generate questionnaires'),
        (PROGRESS_STD_PUBLISHED, 'Publish the study'),
    )
    progress = models.CharField(
        max_length=4,
        choices=PROGRESS,
        default=PROGRESS_STD_CREATED,
    )

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        return super().save(*args, **kwargs)

    @property
    def experiments(self):
        return self.experiment_set.all()

    @property
    def has_text_items(self):
        return self.item_type == self.ITEM_TYPE_TXT

    @property
    def has_audiolink_items(self):
        return self.item_type == self.ITEM_TYPE_AUDIO_LINK

    @property
    def status(self):
        from apps.trial.models import Trial
        if not self.is_published:
            return StudyStatus.DRAFT
        if self.end_date and self.end_date < timezone.now().date():
            return StudyStatus.FINISHED
        if self.trial_limit  and self.trial_limit <= Trial.objects.filter(questionnaire__study=self).count():
            return StudyStatus.FINISHED
        return StudyStatus.ACTIVE

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('study', args=[self.slug])

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

    def _create_next_questionnaire(self, questionnaire_num, last_questionnaire):
        from apps.trial.models import Questionnaire
        questionnaire = Questionnaire.objects.create(number=questionnaire_num, study=self)

        if questionnaire_num == 0:
            questionnaire_item_lists = self._init_questionnaire_lists()
        else:
            questionnaire_item_lists = self._next_questionnaire_lists(last_questionnaire)

        [questionnaire.item_lists.add(item_list) for item_list in questionnaire_item_lists]

        return questionnaire

    def generate_questionnaires(self):
        self.questionnaire_set.all().delete()
        questionnaire_count = self._questionnaire_count()
        last_questionnaire = None
        for i in range(questionnaire_count):
            last_questionnaire = self._create_next_questionnaire(i, last_questionnaire)

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
        for trial in trials:
            csv_row = [
                trial.id,
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
        elif progress == self.PROGRESS_STD_SCALE_CONFIGURED:
            return reverse('study-questions', args=[self])
        elif progress == self.PROGRESS_STD_EXP_CREATED:
            return reverse('experiments', args=[self])
        elif progress == self.PROGRESS_STD_EXP_COMPLETED:
            return reverse('study', args=[self])
        elif progress == self.PROGRESS_STD_QUESTIONNARES_GENERATED:
            return reverse('questionnaires', args=[self])
        elif progress == self.PROGRESS_STD_PUBLISHED:
            return reverse('studies', args=[])
        return None

    def set_progress(self, progress):
        self.progress = progress
        self.save()

    def next_progress_steps(self, progress):
        if progress == self.PROGRESS_STD_CREATED:
            return [ self.PROGRESS_STD_SCALE_CONFIGURED ]
        elif progress == self.PROGRESS_STD_SCALE_CONFIGURED:
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
        max_length=200,
        blank=True,
        null=True,
        help_text='TODO This text will precede the stimulus (e.g. "How acceptable is this sentence?")',
    )
    legend = models.TextField(
        max_length=1024,
        blank=True,
        null=True,
        help_text='TODO This legend will appear below the stimulus to clarify the scale (e.g. "1 = bad, 5 = good").',
    )

    class Meta:
        ordering = ['pk']

    @property
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

    @property
    def num(self):
        return list(ScaleValue.objects.filter(question=self.question)).index(self) + 1

    def __str__(self):
        return self.label
