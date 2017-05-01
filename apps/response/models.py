from django.db import models

from apps.trial import models as trial_models


class UserResponse(models.Model):
    number = models.IntegerField()
    user_trial_item = models.ForeignKey(trial_models.UserTrialItem, on_delete=models.CASCADE)

    class Meta:
        abstract = True

class UserBinaryResponse(UserResponse):
    yes = models.BooleanField()
