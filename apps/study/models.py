from enum import Enum, auto
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone

from apps.contrib import math


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
    rating_instructions = models.TextField(max_length=1024)
    rating_question = models.CharField(max_length=200, blank=True, null=True)
    rating_legend = models.TextField(max_length=1024, blank=True, null=True)
    password = models.CharField(max_length=200)
    allow_anonymous = models.BooleanField()
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)

    PROGRESS_STD_CREATED = '00sc'
    PROGRESS_STD_SCALE_CONFIGURED = '01ss'
    PROGRESS_EXP_CREATED = '02ec'
    PROGRESS_EXP_ITEMS_CREATED = '03ic'
    PROGRESS_EXP_ITEMS_VALIDATED = '04iv'
    PROGRESS_EXP_LISTS_CREATED = '05lc'
    PROGRESS_STD_QUESTIONNARES_GENERATED = '06sq'
    PROGRESS_STD_RUN = '07sq'
    PROGRESS = (
        (PROGRESS_STD_CREATED, 'Create a study'),
        (PROGRESS_STD_SCALE_CONFIGURED, 'Configure the rating scale '),
        (PROGRESS_EXP_CREATED, 'Create a new experiment'),
        (PROGRESS_EXP_ITEMS_CREATED, 'Create or upload experiment items'),
        (PROGRESS_EXP_ITEMS_VALIDATED, 'Validate the experiment items consistancy'),
        (PROGRESS_EXP_LISTS_CREATED, 'Generate item lists'),
        (PROGRESS_STD_QUESTIONNARES_GENERATED, 'Generate questionnaires'),
        (PROGRESS_STD_RUN, 'Run a study'),
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

    def progress_reached(self, progress):
        return self.progress < progress

    @staticmethod
    def progress_description(progress):
        return dict(Study.PROGRESS)[progress]

    def _progress_url(self, progress, experiment=None):
        if progress == self.PROGRESS_STD_CREATED:
            return reverse('study-create', args=[])
        elif progress == self.PROGRESS_STD_SCALE_CONFIGURED:
            return reverse('study-scale', args=[self])
        elif progress == self.PROGRESS_EXP_CREATED:
            return reverse('experiment-create', args=[self])
        elif progress == self.PROGRESS_EXP_ITEMS_CREATED:
            if experiment:
                return reverse('textitems', args=[self, experiment])
        elif progress == self.PROGRESS_EXP_ITEMS_VALIDATED:
            if experiment:
                return reverse('textitems', args=[self, experiment])
        elif progress == self.PROGRESS_EXP_LISTS_CREATED:
            if experiment:
                return reverse('itemlists', args=[self, experiment])
        elif progress == self.PROGRESS_STD_QUESTIONNARES_GENERATED:
            return reverse('questionnaires', args=[self])
        elif progress == self.PROGRESS_STD_RUN:
            return reverse('studies', args=[])
        return None

    def _next_progress_steps(self, progress):
        if progress == self.PROGRESS_STD_CREATED:
            return [self.PROGRESS_STD_SCALE_CONFIGURED]
        elif progress == self.PROGRESS_STD_SCALE_CONFIGURED:
            return [self.PROGRESS_EXP_CREATED]
        elif progress == self.PROGRESS_EXP_CREATED:
            return [self.PROGRESS_EXP_ITEMS_CREATED]
        elif progress == self.PROGRESS_EXP_ITEMS_CREATED:
            return [self.PROGRESS_EXP_ITEMS_CREATED, self.PROGRESS_EXP_ITEMS_VALIDATED]
        elif progress == self.PROGRESS_EXP_ITEMS_VALIDATED:
            return [self.PROGRESS_EXP_LISTS_CREATED]
        elif progress == self.PROGRESS_EXP_LISTS_CREATED:
            return [self.PROGRESS_EXP_CREATED, self.PROGRESS_STD_QUESTIONNARES_GENERATED]
        elif progress == self.PROGRESS_STD_QUESTIONNARES_GENERATED:
            return [ self.PROGRESS_STD_RUN ]
        elif progress == self.PROGRESS_STD_RUN:
            return []

    def next_steps(self, experiment=None):
        for next_step in self._next_progress_steps(self.progress):
            description = self.progress_description(next_step)
            url = self._progress_url(next_step, experiment)
            yield ( description, url, )



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
