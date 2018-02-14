import random
import uuid
from django.db import models
from django.urls import reverse
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
        items = [trial_item.item for trial_item in trial_items]
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
        return reverse('user-trial', args=[self.setup.slug, self.slug])


class UserTrialItem(models.Model):
    number = models.IntegerField()
    user_trial = models.ForeignKey(UserTrial, on_delete=models.CASCADE)
    item = models.ForeignKey(item_models.Item, on_delete=models.CASCADE)

    @property
    def response_text(self):
        from apps.response import models as response_models
        setup = self.user_trial.trial.setup
        try:
            response = self.userresponse
            if response.userbinaryresponse:
                if response.userbinaryresponse.yes:
                    return setup.responsesettings.binaryresponsesettings.yes
                else:
                    return setup.responsesettings.binaryresponsesettings.no
        except response_models.UserResponse.DoesNotExist:
            return ''

