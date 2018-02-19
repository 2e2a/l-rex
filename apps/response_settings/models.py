from django.db import models

from apps.study import models as study_models


class ResponseSettings(models.Model):
    study = models.OneToOneField(
        study_models.Study,
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
