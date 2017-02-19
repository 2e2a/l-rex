from django.conf import settings
from django.db import models
from autoslug import AutoSlugField


class Experiment(models.Model):
    title = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from='title')
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

