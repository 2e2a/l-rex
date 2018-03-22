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
        questionnaire = trial_models.Questionnaire.objects.create(number=questionnaire_num, study=self)

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


class ScaleValue(models.Model):
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
