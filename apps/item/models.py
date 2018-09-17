from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


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
    block = models.IntegerField(
        help_text='TODO',
        default=1
    )

    class Meta:
        ordering = ['block', 'number', 'condition']

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
        verbose_name='URL',
        help_text='Link to the audio file (e.g., https://yourserver.org/item1a.ogg).',
    )

    def get_absolute_url(self):
        return reverse('audiolink-item-update', args=[self.experiment.study.slug, self.experiment.slug, self.pk])


class ItemList(models.Model):
    experiment = models.ForeignKey(
        'lrex_experiment.Experiment',
        on_delete=models.CASCADE
    )
    items = models.ManyToManyField(Item)

    class Meta:
        ordering = ['pk']

    @property
    def num(self):
        return list(ItemList.objects.filter(experiment=self.experiment)).index(self) + 1

    def next(self):
        next_list =  self.experiment.itemlist_set.filter(pk__gt=self.pk).first()
        if not next_list:
            next_list =  ItemList.objects.first()
        return next_list


class ItemQuestion(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE
    )
    question = models.CharField(
        max_length=1000,
        help_text='Individual question text for this item (e.g. "How acceptable is this sentence?")',
    )
    scale_labels = models.CharField(
        max_length=500,
        help_text='Individual rating scale labels for this item, separated by commas (e.g. "1,2,3,4,5"). Note that '
                  'this will only overwrite the displayed labels, but the responses will be saved according to the '
                  'general scale specified in the study settings.',
        blank=True,
        null=True,
    )
    legend = models.CharField(
        max_length=1000,
        help_text='Individual legend for this item to clarify the scale (e.g. "1 = bad, 5 = good")',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['question']
