import random
import uuid
from datetime import datetime, timedelta
from enum import Enum, auto
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.item import models as item_models


class Questionnaire(models.Model):
    number = models.IntegerField()
    study = models.ForeignKey(
        'lrex_study.Study',
        on_delete=models.CASCADE
    )
    item_lists = models.ManyToManyField(item_models.ItemList)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return '{}-{}'.format(self.study, self.number)

    def get_absolute_url(self):
        return reverse('questionnaire', args=[self.study.slug, self.slug])

    @property
    def items(self):
        items = []
        for item_list in self.item_lists.all():
            items.extend(item_list.items.all())
        return items

    @property
    def next(self):
        questionnaire =  self.study.questionnaire_set.filter(number__gt=self.number).first()
        if not questionnaire:
            questionnaire = Questionnaire.objects.first()
        return questionnaire


class TrialStatus(Enum):
    CREATED = auto()
    STARTED = auto()
    FINISHED = auto()
    ABANDOND = auto()


class Trial(models.Model):
    slug = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(
        default=timezone.now
    )
    id = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['creation_date']

    @property
    def items(self):
        items = [trial_item.item for trial_item in self.trialitem_set.all()]
        return items

    @property
    def status(self):
        from apps.results.models import UserResponse
        n_responses = len(UserResponse.objects.filter(trial_item__trial=self))
        if n_responses>0:
            n_trial_items = len(self.items)
            if n_responses == n_trial_items:
                return TrialStatus.FINISHED
            if self.creation_date + timedelta(1) < timezone.now():
                return TrialStatus.ABANDOND
            return TrialStatus.STARTED
        return TrialStatus.CREATED

    def init(self):
        last_trial = Trial.objects.first()
        if last_trial:
            questionnaire = last_trial.questionnaire.next
        else:
            questionnaire = Questionnaire.objects.first()
        self.questionnaire = questionnaire

    def generate_items(self):
        items = self.questionnaire.items
        random.shuffle(items)
        for i, item in enumerate(items):
            TrialItem.objects.create(number=i, trial=self, item=item)

    def get_absolute_url(self):
        return reverse('trial', args=[self.study.slug, self.slug])


class TrialItem(models.Model):
    number = models.IntegerField()
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE)
    item = models.ForeignKey(item_models.Item, on_delete=models.CASCADE)

    class Meta:
        ordering = ['number']
