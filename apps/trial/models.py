import random
import uuid
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.item import models as item_models

class Trial(models.Model):
    number = models.IntegerField()
    study = models.ForeignKey(
        'lrex_study.Study',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['number']

    def __str__(self):
        return '{}-{}'.format(self.study, self.number)

    def get_absolute_url(self):
        return reverse('trial', args=[self.study.slug, self.slug])

    @property
    def lists(self):
        lists = [trial_list.list for trial_list in self.triallist_set.all()]
        return lists

    @property
    def items(self):
        items = []
        for list in self.lists:
            items.extend(list.items)
        return items

    @property
    def next(self):
        trial =  self.study.trial_set.filter(number__gt=self.number).first()
        if not trial:
            trial = Trial.objects.first()
        return trial


class TrialList(models.Model):
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE)
    list = models.ForeignKey(item_models.List, on_delete=models.CASCADE)


class UserTrial(models.Model):
    slug = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(
        default=timezone.now
    )
    id = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['creation_date']

    @property
    def items(self):
        items = [trial_item.item for trial_item in self.usertrialitem_set.all()]
        return items

    def init(self):
        last_user_trial = UserTrial.objects.first()
        if last_user_trial:
            trial = last_user_trial.trial.next
        else:
            trial = Trial.objects.first()
        self.trial = trial

    def generate_items(self):
        items = self.trial.items
        random.shuffle(items)
        for i, item in enumerate(items):
            UserTrialItem.objects.create(number=i, user_trial=self, item=item)

    def get_absolute_url(self):
        return reverse('user-trial', args=[self.study.slug, self.slug])


class UserTrialItem(models.Model):
    number = models.IntegerField()
    user_trial = models.ForeignKey(UserTrial, on_delete=models.CASCADE)
    item = models.ForeignKey(item_models.Item, on_delete=models.CASCADE)

    class Meta:
        ordering = ['number']
