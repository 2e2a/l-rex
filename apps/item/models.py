from markdownx.models import MarkdownxField
from django.db import models
from django.urls import reverse

from apps.contrib.utils import slugify_unique


class Item(models.Model):
    slug = models.SlugField(
        unique=True,
        max_length=230,
    )
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
        help_text='Number of the questionnaire block in which the item will appear',
        default=1
    )

    class Meta:
        ordering = ['number', 'condition']

    @property
    def experiment_block(self):
        if self.experiment.is_example:
            return 0
        if self.experiment.block > 0:
            return self.experiment.block
        return self.block

    @property
    def content(self):
        if hasattr(self, 'textitem'):
            return self.textitem.text
        elif hasattr(self, 'markdownitem'):
            return self.markdownitem.text
        elif hasattr(self, 'audiolinkitem'):
            return self.audiolinkitem.url
        return ''

    def __str__(self):
        return '{}{}'.format(self.number, self.condition)

    def save(self, *args, **kwargs):
        slug = '{}--{}{}'.format(self.experiment.slug, self.number, self.condition)
        new_slug = slugify_unique(slug, Item, self.id)
        if new_slug != self.slug:
            self.slug = slugify_unique(slug, Item, self.id)
        return super().save(*args, **kwargs)


class TextItem(Item):
    text = models.TextField(
        max_length=1024,
        help_text='Content of the item (character limit: 1024)',
    )

    def get_absolute_url(self):
        return reverse('text-item-update', args=[self.experiment.study.slug, self.experiment.slug, self.pk])


class MarkdownItem(Item):
    text = MarkdownxField(
        max_length=1024,
        help_text='Content of the item with markdown formatting (character limit: 1024)',
    )

    def get_absolute_url(self):
        return reverse('markdown-item-update', args=[self.experiment.study.slug, self.experiment.slug, self.pk])


class AudioLinkItem(Item):
    url = models.URLField(
        verbose_name='URL',
        help_text='Link to the audio file (e.g., https://yourserver.org/item1a.ogg).',
    )
    description = MarkdownxField(
        max_length=5000,
        help_text='Additional description shown with the audio item.',
        blank=True,
        null=True,

    )

    def get_absolute_url(self):
        return reverse('audiolink-item-update', args=[self.experiment.study.slug, self.experiment.slug, self.pk])


class ItemList(models.Model):
    experiment = models.ForeignKey(
        'lrex_experiment.Experiment',
        on_delete=models.CASCADE
    )
    number = models.IntegerField(
        default=0,
    )
    items = models.ManyToManyField(Item)

    class Meta:
        ordering = ['experiment', 'number']

    def __str__(self):
        return '{} {}'.format(self.experiment, self.number)

    def next(self):
        next_list =  self.experiment.itemlist_set.filter(pk__gt=self.pk).first()
        if not next_list:
            next_list =  self.experiment.itemlist_set.first()
        return next_list


class ItemQuestion(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE
    )
    number = models.IntegerField(
        default=0,
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
        ordering = ['item', 'number']

    def __str__(self):
        return '{}{}'.format(self.item, self.number)


class ItemFeedback(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        help_text='Item for the feedback.',
    )
    question = models.ForeignKey(
        'lrex_study.Question',
        on_delete=models.CASCADE,
        help_text='Question for the feedback.',
    )
    scale_values = models.CharField(
        max_length=500,
        help_text='Scale values, separated by commas (e.g. "1,3"). The feedback will be shown to the '
                  'participant if one of these ratings is selected.'
    )
    feedback = models.TextField(
        max_length=5000,
        help_text='Feedback shown to the participant for the selected rating scale values.',
    )

    class Meta:
        ordering = ['item', 'question']

    def show_feedback(self, scale_value):
        return scale_value.label in self.scale_values.split(',')
