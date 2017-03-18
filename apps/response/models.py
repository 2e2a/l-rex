from django.db import models

from apps.experiment import models as experiment_models


class Response(models.Model):
    experiment = models.ForeignKey(
        experiment_models.Experiment,
        on_delete=models.CASCADE
    )
    question = models.CharField(max_length=200)
    legend = models.TextField(max_length=1024)

    class Meta:
        abstract = True

    def __str__(self):
        return '{}-response'.format(self.experiment)


class BinaryResponse(Response):
    yes = models.CharField(max_length=200)
    no = models.CharField(max_length=200)
