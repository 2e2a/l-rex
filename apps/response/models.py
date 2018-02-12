from django.db import models

from apps.setup import models as setup_models
from apps.trial import models as trial_models


class ResponseSettings(models.Model):
    setup = models.OneToOneField(
        setup_models.Setup,
        on_delete=models.CASCADE
    )
    question = models.CharField(max_length=200)
    legend = models.TextField(max_length=1024)
    instructions = models.TextField(max_length=1024)
    RESPONSE_TYPE = (
        ('bin', 'Binary'),
    )
    reponse_type = models.CharField(
        max_length=3,
        choices=RESPONSE_TYPE,
        default='bin',
    )

    @property
    def is_binary_response(self):
        return self.reponse_type is 'bin'


class BinaryResponseSettings(ResponseSettings):
    yes = models.CharField(max_length=200)
    no = models.CharField(max_length=200)

class UserResponse(models.Model):
    number = models.IntegerField()
    user_trial_item = models.ForeignKey(trial_models.UserTrialItem, on_delete=models.CASCADE)

    class Meta:
        abstract = True

class UserBinaryResponse(UserResponse):
    yes = models.BooleanField()
