from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models

class Item(models.Model):
    number = models.IntegerField()
    condition = models.CharField(max_length=8)
    experiment = models.ForeignKey(
        'lrex_experiment.Experiment',
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
        ordering = ['number', 'condition']

    def __str__(self):
        return '{}-{}-{}'.format(self.experiment, self.number, self.condition)


class TextItem(Item):
    text = models.TextField(max_length=1024)

    def get_absolute_url(self):
        return reverse('experiment', args=[self.experiment.setup.slug, self.experiment.slug])


class List(models.Model):
    number = models.IntegerField()
    experiment = models.ForeignKey(
        'lrex_experiment.Experiment',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['number']

    def items(self):
        list_items = ListItem.objects.filter(list=self)
        items = [list_item.content_object for list_item in list_items]
        return items

    def __str__(self):
        return '{}-list-{}'.format(self.experiment, self.number)


class ListItem(models.Model):
    list = models.ForeignKey(List, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
