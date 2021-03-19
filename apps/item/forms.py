import re
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, HTML, Layout, Submit
from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory

from apps.contrib import csv as contrib_csv
from apps.contrib import forms as contrib_forms
from apps.contrib.utils import split_list_string
from apps.study import forms as study_forms
from apps.study import models as study_models

from . import models


class ItemFormMixin:

    def clean_condition(self):
        return self.cleaned_data['condition'].strip()

    def __init__(self, *args, **kwargs):
        materials = kwargs.pop('materials')
        super().__init__(*args, **kwargs)
        if not materials.study.use_blocks or materials.is_example or materials.block > 0:
            self.fields['block'].widget = forms.HiddenInput()


class TextItemForm(ItemFormMixin, contrib_forms.CrispyModelForm):

    class Meta:
        model = models.TextItem
        fields = ['number', 'condition', 'text', 'block']


class MarkdownItemForm(ItemFormMixin, contrib_forms.CrispyModelForm):

    class Meta:
        model = models.MarkdownItem
        fields = ['number', 'condition', 'text', 'block']


def clean_url_list(urls):
    return urls.replace(' ', '').replace('\n', '')


def validate_urls(urls):
    url_list = [url.strip() for url in urls.split(',')]
    validator = URLValidator()
    for url in url_list:
        try:
            validator(url)
        except ValidationError:
            raise ValidationError(
                '"{}" is not a valid URL.'.format(url)
            )


class AudioLinkItemForm(ItemFormMixin, contrib_forms.CrispyModelForm):

    class Meta:
        model = models.AudioLinkItem
        fields = ['number', 'condition', 'urls', 'description', 'block']

    def clean_urls(self):
        urls = self.cleaned_data['urls']
        validate_urls(urls)
        return clean_url_list(urls)


class PregenerateItemsForm(contrib_forms.CrispyForm):
    num_items = forms.IntegerField(
        label='number of items',
        help_text='Empty text fields will be pregenerated to accommodate this number of items.',
    )
    num_conditions = forms.IntegerField(
        label='number of conditions',
        help_text='Empty text fields will be pregenerated to accommodate this number of conditions.',
    )


class ItemUploadForm(contrib_forms.CSVUploadForm):
    file = forms.FileField(
        help_text='The CSV file must contain columns for item number, condition, and text/link to the audio file. '
                  'Valid column delimiters: colon, semicolon, comma, space, or tab.',
        widget=forms.FileInput,
    )
    number_column = forms.IntegerField(
        initial=1,
        help_text='Specify which column contains the item number.',
    )
    condition_column = forms.IntegerField(
        initial=2,
        help_text='Specify which column contains the condition.',
    )
    content_column = forms.IntegerField(
        initial=3,
    )
    block_column = forms.IntegerField(
        initial=0,
        help_text='Optional: specify which column contains the questionnaire block. '
                  'Set to 0 if the questionnaire does not contain more than one block.',
    )

    validator_int_columns = ['number_column']

    def __init__(self, *args, **kwargs):
        self.materials = kwargs.pop('materials')
        self.study = self.materials.study
        super().__init__(*args, **kwargs)
        if self.study.has_text_items:
            content_help_text = 'Specify which column contains the item text.'
        elif self.study.has_markdown_items:
            content_help_text = 'Specify which column contains the item text formatted with markdown.'
        elif self.study.has_audiolink_items:
            content_help_text = 'Specify which column contains the link to the audio file.'
            self.fields.update(
                {
                    'audio_description_column':
                        forms.IntegerField(
                            initial=0,
                            help_text='Optional: specify which column contains a description shown with the audio item.'
                        )
                }
            )

        self.fields['content_column'].help_text = content_help_text
        if not self.study.use_blocks or self.materials.is_example or self.materials.block > 0:
            self.fields['block_column'].widget = forms.HiddenInput()
        for question in self.study.questions.all():
            self.fields.update(
                {
                    'question_{}_question_column'.format(question.number + 1):
                    forms.IntegerField(
                        initial=0,
                        help_text='Optional: specify which column contains the item-specific question. '
                                  'Set to 0 to use the default question as specified in the study settings.'
                     )
                }
            )
            self.fields.update(
                {
                    'question_{}_scale_column'.format(question.number + 1):
                        forms.IntegerField(
                            initial=0,
                            help_text='Optional: specify which column contains the item-specific '
                                      'question scale values (comma-separated). '
                                      'Set to 0 to use the default scale values as specified in the study settings.'
                        )
                }
            )
            self.fields.update(
                {
                    'question_{}_legend_column'.format(question.number + 1):
                        forms.IntegerField(
                            initial=0,
                            help_text='Optional: specify which column contains the items-specific scale legend. '
                                      'Set to 0 to use the default legend as specified in the study settings.'
                        )
                }
            )

    def check_upload_form(self, reader, cleaned_data):
        min_columns = contrib_csv.get_min_columns(cleaned_data)
        for row in reader:
            if not row:
                continue
            assert len(row) >= min_columns
            int(row[cleaned_data['number_column'] - 1])
            assert row[cleaned_data['condition_column'] - 1]
            assert len(row[cleaned_data['condition_column'] - 1]) <= 16
            assert row[cleaned_data['content_column'] - 1]
            if self.study.has_audiolink_items:
                validate_urls(row[cleaned_data['content_column'] - 1])
            if cleaned_data['block_column'] > 0:
                int(row[cleaned_data['block_column'] - 1])
            for question in self.study.questions.all():
                if cleaned_data['question_{}_question_column'.format(question.number + 1)] > 0:
                    assert row[cleaned_data['question_{}_question_column'.format(question.number + 1)] - 1]
                if cleaned_data['question_{}_scale_column'.format(question.number + 1)] > 0:
                    assert row[cleaned_data['question_{}_scale_column'.format(question.number + 1)] - 1]
                    scale_values = split_list_string(
                        row[cleaned_data['question_{}_scale_column'.format(question.number + 1)] - 1]
                    )
                    assert len(scale_values) == question.scale_values.count()
                    assert all(
                        len(scale_value) <= study_models.ScaleValue.LABEL_MAX_LENGTH for scale_value in scale_values
                    )
                if cleaned_data['question_{}_legend_column'.format(question.number + 1)] > 0:
                    assert row[cleaned_data['question_{}_legend_column'.format(question.number + 1)] - 1]


class ItemQuestionForm(contrib_forms.CrispyModelForm):

    class Meta:
        model = models.ItemQuestion
        fields = ['question', 'scale_labels', 'legend', 'number']
        field_classes = {
            'scale_labels': study_forms.ScaleLabelsListField,
        }
        widgets = {
            'number': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        self.question = kwargs.pop('question')
        super().__init__(*args, **kwargs)
        self.append_optional_to_labels()
        self.fields['number'].initial = self.question.number
        self.fields['question'].initial = self.question.question
        self.fields['scale_labels'].initial = self.question.scale_labels
        self.fields['legend'].initial = self.question.legend

    def clean_scale_labels(self):
        data = self.cleaned_data['scale_labels']
        scale_labels = split_list_string(data)
        if len(scale_labels) != self.question.scale_values.count():
                raise ValidationError('Invalid scale label number. Must match the original ???')
        return data


class ItemQuestionFormset(forms.BaseModelFormSet):

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        study = kwargs.get('study')
        kwargs['question'] = study.questions.filter(number=index).first()
        return kwargs


class ItemQuestionFormsetFactory(contrib_forms.CrispyModelFormsetFactory):
    model = models.ItemQuestion
    form = ItemQuestionForm

    @staticmethod
    def get_layout(study=None):
        return Layout(
            Fieldset(
                'Question {{ forloop.counter }}', None, 'question', 'scale_labels', 'legend', HTML('<hr>')
            ),
        )


class ItemFeedbackUploadForm(contrib_forms.CSVUploadForm):
    file = forms.FileField(
        help_text='The CSV file must contain a column for the item number, condition, question, scale-values and '
                  'feedback. Valid column delimiters: colon, semicolon, comma, space, or tab.',
        widget=forms.FileInput,
    )
    item_number_column = forms.IntegerField(
        initial=1,
        help_text='Specify which column contains the item number.',
    )
    item_condition_column = forms.IntegerField(
        initial=2,
        help_text='Specify which column contains the item condition.',
    )
    question_column = forms.IntegerField(
        initial=3,
        help_text='Specify which column contains the question number.',
    )
    scale_values_column = forms.IntegerField(
        initial=4,
        help_text='Specify which column contains the question scale values (comma-separated).',
    )
    feedback_column = forms.IntegerField(
        initial=5,
        help_text='Specify which column contains the feedback.',
    )

    validator_int_columns = ['item_number_column', 'question_column']

    def __init__(self, *args, **kwargs):
        self.materials = kwargs.pop('materials')
        super().__init__(*args, **kwargs)

    def check_upload_form(self, reader, cleaned_data):
        for row in reader:
            item_num = int(row[cleaned_data['item_number_column'] - 1])
            item_cond = row[cleaned_data['item_condition_column'] - 1]
            assert item_cond
            item_exists = models.Item.objects.filter(
                materials=self.materials,
                number=item_num,
                condition=item_cond,
            ).exists()
            if not item_exists:
                raise forms.ValidationError('Item {}{} does not exist.'.format(item_num, item_cond))
            question_num = int(row[cleaned_data['question_column'] - 1]) - 1
            question = self.materials.study.get_question(question_num)
            if not question:
                raise forms.ValidationError('Question {} does not exist.'.format(question_num))
            scale_values = row[cleaned_data['scale_values_column'] - 1]
            assert scale_values
            if not all(question.is_valid_scale_value(scale_value) for scale_value in scale_values):
                raise forms.ValidationError('Invalid scale values: {}.'.format(scale_values))
            assert row[cleaned_data['feedback_column'] - 1]


class ItemListUploadForm(contrib_forms.CSVUploadForm):
    file = forms.FileField(
        help_text='The CSV file must contain a column for the item list number, item number and condition.'
                  'Valid column delimiters: colon, semicolon, comma, space, or tab.',
        widget=forms.FileInput,
    )
    list_column = forms.IntegerField(
        initial=1,
        help_text='Specify which column contains the item list number.',
    )
    items_column = forms.IntegerField(
        initial=2,
        help_text='Specify which column contains the materials items.'
                  'Format: comma-separated list of <Item>-<Condition> (e.g. Filler-1a,Exp-2b,...).'
    )

    validator_int_columns = ['list_column']

    def __init__(self, *args, **kwargs):
        self.materials = kwargs.pop('materials')
        super().__init__(*args, **kwargs)

    @staticmethod
    def read_items(items_string, materials_items):
        items = []
        item_strings = items_string.split(',')
        for item_string in item_strings:
            pattern = re.compile('(\d+)(\D+)')
            match = pattern.match(item_string)
            if not match or len(match.groups()) != 2:
                raise forms.ValidationError('Not a valid item format "{}".'.format(item_string))
            try:
                item_num = int(match.group(1))
            except ValueError:
                raise forms.ValidationError('Not a valid item format "{}".'.format(item_string))
            item_cond = match.group(2)
            item_match = None
            for item in materials_items:
                if item.number == item_num and item.condition == item_cond:
                    item_match = item
                    break
            if item_match:
                items.append(item_match)
            else:
                raise forms.ValidationError('Item {} does not exist.'.format(item_string))
        return items

    def check_upload_form(self, reader, cleaned_data):
        materials_items = list(self.materials.items.all())
        for row in reader:
            int(row[cleaned_data['list_column'] - 1])
            items_string = row[cleaned_data['items_column'] - 1]
            self.read_items(items_string, materials_items)


class ItemFeedbackForm(contrib_forms.CrispyModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.append_optional_to_labels()
        self.fields['question'].queryset = self.fields['question'].queryset.filter(study=self.study)
        self.fields['question'].empty_label = None

    class Meta:
        model = models.ItemFeedback
        fields = ['question', 'scale_values', 'feedback']

    def clean(self):
        data = super().clean()
        question = data['question']
        scale_values = split_list_string(data['scale_values'])
        if not all(question.is_valid_scale_value(scale_value) for scale_value in scale_values):
            raise ValidationError('Invalid scale values')


class ItemFeedbackFormsetFactory(contrib_forms.CrispyModelFormsetFactory):
    model = models.ItemFeedback
    form = ItemFeedbackForm

    @staticmethod
    def get_layout(study=None):
        return Layout(
            Fieldset(
                'Feedback {{ forloop.counter }}', None, 'question', 'scale_values', 'feedback',
                'DELETE', HTML('<hr>')
            ),
        )
