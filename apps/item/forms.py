import csv
import re
from io import StringIO
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit
from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory

from apps.contrib import csv as contrib_csv
from apps.contrib import forms as crispy_forms

from . import models


class ItemFormMixin:

    def clean_condition(self):
        return self.cleaned_data['condition'].strip()

    def __init__(self, *args, **kwargs):
        experiment = kwargs.pop('experiment')
        super().__init__(*args, **kwargs)
        if not experiment.study.use_blocks or experiment.is_example or experiment.block > 0:
            self.fields['block'].widget = forms.HiddenInput()


class TextItemForm(ItemFormMixin, crispy_forms.CrispyModelForm):

    class Meta:
        model = models.TextItem
        fields = ['number', 'condition', 'text', 'block']


class MarkdownItemForm(ItemFormMixin, crispy_forms.CrispyModelForm):

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


class AudioLinkItemForm(ItemFormMixin, crispy_forms.CrispyModelForm):

    class Meta:
        model = models.AudioLinkItem
        fields = ['number', 'condition', 'urls', 'description', 'block']

    def clean_urls(self):
        urls = self.cleaned_data['urls']
        validate_urls(urls)
        return clean_url_list(urls)


class PregenerateItemsForm(crispy_forms.CrispyForm):
    num_items = forms.IntegerField(
        label='number of items',
        help_text='Empty text fields will be pregenerated to accommodate this number of items.',
    )
    num_conditions = forms.IntegerField(
        label='number of conditions',
        help_text='Empty text fields will be pregenerated to accommodate this number of conditions.',
    )


class ItemUploadForm(crispy_forms.CSVUploadForm):
    file = forms.FileField(
        help_text='The CSV file must contain columns for item number, condition, and text/link to the audio file. '
                  'Valid column delimiters: colon, semicolon, comma, space, or tab.',
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
        self.experiment = kwargs.pop('experiment')
        self.study = self.experiment.study
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
        if not self.study.use_blocks or self.experiment.is_example or self.experiment.block > 0:
            self.fields['block_column'].widget = forms.HiddenInput()
        for question in self.study.questions:
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
            assert len(row[cleaned_data['condition_column'] - 1]) < 8
            assert row[cleaned_data['content_column'] - 1]
            if self.study.has_audiolink_items:
                validate_urls(row[cleaned_data['content_column'] - 1])
            if cleaned_data['block_column'] > 0:
                int(row[cleaned_data['block_column'] - 1])
            for question in self.study.questions:
                if cleaned_data['question_{}_question_column'.format(question.number + 1)] > 0:
                    assert row[cleaned_data['question_{}_question_column'.format(question.number + 1)] - 1]
                if cleaned_data['question_{}_scale_column'.format(question.number + 1)] > 0:
                    assert row[cleaned_data['question_{}_scale_column'.format(question.number + 1)] - 1]
                    assert len(
                        row[cleaned_data['question_{}_scale_column'.format(question.number + 1)] - 1].split(',')) == \
                           question.scalevalue_set.count()
                if cleaned_data['question_{}_legend_column'.format(question.number + 1)] > 0:
                    assert row[cleaned_data['question_{}_legend_column'.format(question.number + 1)] - 1]


class ItemQuestionForm(crispy_forms.OptionalLabelMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.append_optional_to_labels()

    class Meta:
        model = models.ItemQuestion
        fields = ['question', 'scale_labels', 'legend']


def itemquestion_formset_factory(n_questions):
    return modelformset_factory(
        models.ItemQuestion,
        form=ItemQuestionForm,
        min_num=n_questions,
        max_num=n_questions,
        extra=0,
    )


def initialize_with_questions(itemquestion_formset, questions):

    def get_question(num, questions):
        for question in questions:
            if question.number == num:
                return question

    for i, form in enumerate(itemquestion_formset):
        question = get_question(i, questions)
        if not form['question'].initial:
            form['question'].initial = question.question
            form['scale_labels'].initial = question.scale_labels
            form['legend'].initial = question.legend


def itemquestion_formset_helper():
    formset_helper = FormHelper()
    formset_helper.add_layout(
        Layout(Fieldset('Question {{ forloop.counter }}', None, 'question', 'scale_labels', 'legend'))
    )
    formset_helper.add_input(Submit('submit', 'Submit'))
    formset_helper.add_input(Submit('save', 'Save', css_class='btn-secondary'))
    formset_helper.add_input(Submit('reset', 'Reset'))
    return formset_helper


class ItemFeedbackUploadForm(crispy_forms.CSVUploadForm):
    file = forms.FileField(
        help_text='The CSV file must contain a column for the item number, condition, question, scale-values and '
                  'feedback. Valid column delimiters: colon, semicolon, comma, space, or tab.',
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
        self.experiment = kwargs.pop('experiment')
        super().__init__(*args, **kwargs)

    def check_upload_form(self, reader, cleaned_data):
        for row in reader:
            item_num = int(row[cleaned_data['item_number_column'] - 1])
            item_cond = row[cleaned_data['item_condition_column'] - 1]
            assert item_cond
            item_exists = models.Item.objects.filter(
                experiment=self.experiment,
                number=item_num,
                condition=item_cond,
            ).exists()
            if not item_exists:
                raise forms.ValidationError('Item {}{} does not exist.'.format(item_num, item_cond))
            question_num = int(row[cleaned_data['question_column'] - 1]) - 1
            question = self.experiment.study.get_question(question_num)
            if not question:
                raise forms.ValidationError('Question {} does not exist.'.format(question_num))
            scale_values = row[cleaned_data['scale_values_column'] - 1]
            assert scale_values
            if not all(question.is_valid_scale_value(scale_value) for scale_value in scale_values):
                raise forms.ValidationError('Invalid scale values {}.'.format(scale_values))
            assert row[cleaned_data['feedback_column'] - 1]


class ItemListUploadForm(crispy_forms.CSVUploadForm):
    file = forms.FileField(
        help_text='The CSV file must contain a column for the item list number, item number and condition.'
                  'Valid column delimiters: colon, semicolon, comma, space, or tab.',
    )
    list_column = forms.IntegerField(
        initial=1,
        help_text='Specify which column contains the item list number.',
    )
    items_column = forms.IntegerField(
        initial=2,
        help_text='Specify which column contains the experiment items.'
                  'Format: comma-separated list of <Item>-<Condition> (e.g. Filler-1a,Exp-2b,...).'
    )

    validator_int_columns = ['list_column']

    def __init__(self, *args, **kwargs):
        self.experiment = kwargs.pop('experiment')
        super().__init__(*args, **kwargs)

    @staticmethod
    def read_items(experiment, items_string):
        items = []
        error_msg = None
        item_strings = items_string.split(',')
        for item_string in item_strings:
            pattern = re.compile('(\d+)(\D+)')
            match = pattern.match(item_string)
            if not match or len(match.groups()) != 2:
                error_msg = 'Not a valid item format "{}".'.format(item_string)
                break
            item_num = match.group(1)
            item_cond = match.group(2)
            try:
                item = models.Item.objects.get(
                    experiment=experiment,
                    number=item_num,
                    condition=item_cond,
                )
                items.append(item)
            except models.Item.DoesNotExist:
                error_msg = 'Item {} does not exist.'.format(item_string)
                break
        if error_msg:
            raise forms.ValidationError(error_msg)
        return items

    def check_upload_form(self, reader, cleaned_data):
        used_items = set()
        for row in reader:
            int(row[cleaned_data['list_column'] - 1])
            items_string = row[cleaned_data['items_column'] - 1]
            used_items.update(self.read_items(self.experiment, items_string))
        if not len(used_items) == models.Item.objects.filter(experiment=self.experiment).count():
            raise forms.ValidationError('Not all items used in lists.')


class ItemFeedbackForm(crispy_forms.OptionalLabelMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.append_optional_to_labels()

    class Meta:
        model = models.ItemFeedback
        fields = ['question', 'scale_values', 'feedback']


def itemfeedback_formset_factory(extra=0):
    return modelformset_factory(
        models.ItemFeedback,
        form=ItemFeedbackForm,
        extra=extra,
    )


def itemfeedback_init_formset(itemfeedback_formset, study):

    for form in itemfeedback_formset:
        question = form.fields.get('question')
        question.queryset = question.queryset.filter(study=study)
        question.empty_label = None


def itemfeedback_formset_helper():
    formset_helper = FormHelper()
    formset_helper.add_layout(
        Layout(Fieldset('Feedback {{ forloop.counter }}', None, 'question', 'scale_values', 'feedback'))
    )
    formset_helper.add_input(Submit('submit', 'Submit'))
    formset_helper.add_input(Submit('save', 'Save', css_class='btn-secondary'))
    formset_helper.add_input(Submit('add', 'Add', css_class='btn-secondary'))
    formset_helper.add_input(Submit('delete', 'Delete last', css_class='btn-danger'))
    return formset_helper
