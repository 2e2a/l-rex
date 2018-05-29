from django.urls import reverse
from django.db import models


class Item(models.Model):
    number = models.IntegerField(
        help_text='Number of the item',
    )
    condition = models.CharField(
        max_length=8,
        help_text='Condition of the item (character limit: 8)',
    )
    experiment = models.ForeignKey(
        'lrex_experiment.Experiment',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['number', 'condition']

    def __str__(self):
        return '{}{}'.format(self.number, self.condition)


class TextItem(Item):
    text = models.TextField(
        max_length=1024,
        help_text='Content of the item (character limit: 1024).',
    )

    def get_absolute_url(self):
        return reverse('text-item-update', args=[self.experiment.study.slug, self.experiment.slug, self.pk])


class AudioLinkItem(Item):
    url = models.URLField(
        help_text='TODO',
    )

    def get_absolute_url(self):
        return reverse('audiolink-item-update', args=[self.experiment.study.slug, self.experiment.slug, self.pk])


class ItemList(models.Model):
    number = models.IntegerField()
    experiment = models.ForeignKey(
        'lrex_experiment.Experiment',
        on_delete=models.CASCADE
    )
    items = models.ManyToManyField(Item)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return '{}-list-{}'.format(self.experiment, self.number)

    def next(self):
        next_list =  self.experiment.itemlist_set.filter(number__gt=self.number).first()
        if not next_list:
            next_list =  ItemList.objects.first()
        return next_list
