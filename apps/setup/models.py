from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from autoslug import AutoSlugField

from apps.experiment import models as experiment_models


class Setup(models.Model):
    title = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from='title', unique=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def experiments(self):
        return experiment_models.Experiment.objects.filter(setup=self)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('setup', args=[self.slug])
