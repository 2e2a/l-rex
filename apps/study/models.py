from enum import Enum, auto
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone

from apps.contrib import math
from apps.trial import models as trial_models


class StudyStatus(Enum):
    PENDING = auto()
    ACTIVE = auto()
    FINISHED = auto()

class Study(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ITEM_TYPE = (
        ('txt', 'Text'),
    )
    item_type = models.CharField(
        max_length=3,
        choices=ITEM_TYPE,
        default='txt',
    )
    response_instructions = models.TextField(max_length=1024)
    response_question = models.CharField(max_length=200, blank=True, null=True)
    response_legend = models.TextField(max_length=1024, blank=True, null=True)
    password = models.CharField(max_length=200)
    allow_anonymous = models.BooleanField()
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        return super().save(*args, **kwargs)

    @property
    def experiments(self):
        return self.experiment_set.all()

    @property
    def is_textitem(self):
        return self.item_type == 'txt'

    @property
    def status(self):
        if self.start_time and self.end_time:
            if self.start_time < timezone.now():
                if self.end_time < timezone.now():
                    return StudyStatus.FINISHED
            else:
                return StudyStatus.PENDING
        return StudyStatus.ACTIVE

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('study', args=[self.slug])

    def _trial_count(self):
        trial_lcm = 1
        for experiment in self.experiment_set.all():
            condition_count = len(experiment.conditions)
            trial_lcm = math.lcm(trial_lcm,  condition_count)
        return trial_lcm

    def _init_trail_lists(self):
        lists = []
        for experiment in self.experiment_set.all():
            list = experiment.list_set.first()
            lists.append(list)
        return lists

    def _next_trail_lists(self, last_trial):
        lists = []
        last_lists = last_trial.lists
        for last_list in last_lists:
            list = last_list.next()
            lists.append(list)
        return lists

    def _create_next_trial(self, trial_num, last_trial):
        trial = trial_models.Trial.objects.create(number=trial_num, study=self)

        if trial_num == 0:
            lists = self._init_trail_lists()
        else:
            lists = self._next_trail_lists(last_trial)

        for list in lists:
            trial_models.TrialList.objects.create(trial=trial, list=list)

        return trial

    def generate_trials(self):
        self.trial_set.all().delete()
        trial_count = self._trial_count()
        last_trial = None
        for i in range(trial_count):
            last_trial = self._create_next_trial(i, last_trial)


class Response(models.Model):
    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE
    )
    number = models.IntegerField()
    label = models.CharField(max_length=50)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return self.label
