from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.contrib.utils import slugify_unique


class News(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(
        max_length=200,
    )
    text = models.TextField(
        max_length=5000,
    )
    date = models.DateTimeField(
        default=timezone.now,
    )

    class Meta:
        ordering = ['date']

    def save(self, *args, **kwargs):
        new_slug = slugify_unique(self.title, News, self.id)
        if self.slug != new_slug:
            self.slug = slugify_unique(self.title, News, self.id)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('news', args=[self.slug])
