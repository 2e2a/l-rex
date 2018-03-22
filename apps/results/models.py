from django.db import models

from apps.study import models as study_models
from apps.trial import models as trial_models


class UserResponse(models.Model):
    number = models.IntegerField()
    trial_item = models.OneToOneField(trial_models.TrialItem, on_delete=models.CASCADE)
    scale_value = models.ForeignKey(study_models.ScaleValue, on_delete=models.CASCADE)

