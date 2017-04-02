import random
import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone

from apps.item import models as item_models

class Trial(models.Model):
    number = models.IntegerField()
    setup = models.ForeignKey(
        'lrex_setup.Setup',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['number']

    def __str__(self):
        return '{}-{}'.format(self.setup, self.number)

    def get_absolute_url(self):
        return reverse('trial', args=[self.setup.slug, self.slug])

    @property
    def lists(self):
        trial_lists = TrialList.objects.filter(trial=self)
        lists = [trial_list.list for trial_list in trial_lists]
        return lists

    @property
    def items(self):
        items = []
        for list in self.lists:
            items.extend(list.items)
        return items

    @property
    def next(self):
        trial =  Trial.objects.filter(setup=self.setup, number__gt=self.number).first()
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
    participant = models.EmailField(blank=True)

    class Meta:
        ordering = ['-creation_date']

    @property
    def items(self):
        trial_items = UserTrialItem.objects.filter(user_trial=self)
        items = [trial_item.content_object for trial_item in trial_items]
        return items

    def generate(self):
        last_user_trial = UserTrial.objects.last()
        if last_user_trial:
            trial = last_user_trial.trial.next
        else:
            trial = Trial.objects.first()
        self.trial = trial

        items = self.trial.items
        random.shuffle(items)
        for i, item in enumerate(items):
            UserTrialItem.objects.create(number=i, user_trial=self, content_object=item)

    def get_absolute_url(self):
        return reverse('user-trial', args=[self.setup.slug, self.slug])


class UserTrialItem(models.Model):
    number = models.IntegerField()
    user_trial = models.ForeignKey(UserTrial, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
