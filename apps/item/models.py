from markdownx.models import MarkdownxField
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from apps.contrib.utils import slugify_unique, split_list_string, strip_html_in_markdown_fields
from apps.study.models import ScaleValue


class Item(models.Model):
    slug = models.SlugField(
        unique=True,
        max_length=230,
    )
    number = models.IntegerField(
        help_text='Number of the item.',
    )
    condition = models.CharField(
        max_length=16,
        help_text='Condition of the item (character limit: 16).',
    )
    materials = models.ForeignKey(
        'lrex_materials.Materials',
        on_delete=models.CASCADE,
        null=True,
        related_name='items',
    )
    block = models.IntegerField(
        help_text='Number of the questionnaire block in which the item will appear.',
        default=1
    )

    class Meta:
        ordering = ['number', 'condition']

    @property
    def materials_block(self):
        if self.materials.is_example:
            return 0
        if self.materials.block > 0:
            return self.materials.block
        return self.block

    def content(self, study):
        if study.has_text_items:
            return self.textitem.text
        elif study.has_markdown_items:
            return self.markdownitem.text
        elif study.has_audiolink_items:
            return self.audiolinkitem.urls
        return ''

    def __str__(self):
        return '{}{}'.format(self.number, self.condition)

    def save(self, *args, **kwargs):
        self.slug = slugify_unique('{}-{}{}'.format(self.materials.slug, self.number, self.condition), Item, self.pk)
        return super().save(*args, **kwargs)


class TextItem(Item):
    text = models.TextField(
        max_length=1024,
        help_text='Content of the item (character limit: 1024).',
    )

    def get_absolute_url(self):
        return reverse('text-item-update', args=[self.slug])


class MarkdownItem(Item):
    text = MarkdownxField(
        max_length=1024,
        help_text='Content of the item with markdown formatting (character limit: 1024).',
    )

    def get_absolute_url(self):
        return reverse('markdown-item-update', args=[self.slug])

    def save(self, *args, **kwargs):
        strip_html_in_markdown_fields(MarkdownItem, self)
        return super().save(*args, **kwargs)


class AudioLinkItem(Item):
    urls = models.TextField(
        max_length=5000,
        verbose_name='URLs',
        help_text='Links to the audio files separated by commas '
                  '(e.g., https://yourserver.org/item1a-i.ogg,https://yourserver.org/item1a-ii.ogg). ',
    )
    description = MarkdownxField(
        max_length=5000,
        help_text='Additional description presented with the audio item.',
        blank=True,
        null=True,

    )

    def save(self, *args, **kwargs):
        strip_html_in_markdown_fields(AudioLinkItem, self)
        return super().save(*args, **kwargs)

    @cached_property
    def urls_list(self):
        return [url.strip() for url in self.urls.split(',')]

    @cached_property
    def has_multiple_urls(self):
        return len(self.urls_list) > 1

    def get_absolute_url(self):
        return reverse('audio-link-item-update', args=[self.slug])


class ItemList(models.Model):
    materials = models.ForeignKey(
        'lrex_materials.Materials',
        on_delete=models.CASCADE,
        null=True,
        related_name='lists',
    )
    number = models.IntegerField(
        default=0,
    )
    items = models.ManyToManyField(Item)

    class Meta:
        ordering = ['materials', 'number']

    def __str__(self):
        return '{}-{}'.format(self.materials, self.number)


class ItemQuestion(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='item_questions'
    )
    number = models.IntegerField(
        default=0,
    )
    question = models.CharField(
        max_length=1000,
        help_text='Individual question text for this item (e.g. "How acceptable is this sentence?").',
    )
    scale_labels = models.TextField(
        max_length=(10 * ScaleValue.LABEL_MAX_LENGTH),
        help_text='Individual rating scale labels for this item, separated by commas (e.g. "1,2,3,4,5"). '
                  'If a label contains a comma itself, escape it with "\\" (e.g. "A,B,Can\'t decide\\, I like both"). '
                  'Note that this will only overwrite the displayed labels, but the responses will be saved according '
                  'to the general scale specified in the study settings.',
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
        related_name='item_feedback',
    )
    question = models.ForeignKey(
        'lrex_study.Question',
        on_delete=models.CASCADE,
        help_text='Question for the feedback.',
    )
    scale_values = models.TextField(
        max_length=(10 * ScaleValue.LABEL_MAX_LENGTH),
        help_text='Scale values, separated by commas (e.g. "1,3"). '
                  'If a label contains a comma itself, escape it with "\\" (e.g. "A,B,Can\'t decide\\, I like both"). '
                  'The feedback will be shown to the participant if one of these ratings is selected.'
    )
    feedback = models.TextField(
        max_length=5000,
        help_text='Feedback shown to the participant for the selected rating scale values.',
    )

    class Meta:
        ordering = ['item', 'question', 'pk']

    def show_feedback(self, scale_value):
        return scale_value.label in split_list_string(self.scale_values)
