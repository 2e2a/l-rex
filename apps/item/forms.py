import csv
import re
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit
from django import forms
from django.forms import modelformset_factory
from io import StringIO

from apps.contrib import csv as contrib_csv
from apps.contrib import forms as crispy_forms

from . import models


class ItemFormMixin:

    def clean_condition(self):
        return self.cleaned_data['condition'].strip()

    def __init__(self, *args, **kwargs):
        study = kwargs.pop('study')
        super().__init__(*args, **kwargs)
        if not study.use_blocks:
            self.fields['block'].widget = forms.HiddenInput()


class TextItemForm(ItemFormMixin, crispy_forms.CrispyModelForm):

    class Meta:
        model = models.TextItem
        fields = ['number', 'condition', 'text', 'block']


class MarkdownItemForm(ItemFormMixin, crispy_forms.CrispyModelForm):

    class Meta:
        model = models.MarkdownItem
        fields = ['number', 'condition', 'text', 'block']


class AudioLinkItemForm(ItemFormMixin, crispy_forms.CrispyModelForm):

    class Meta:
        model = models.AudioLinkItem
        fields = ['number', 'condition', 'url', 'block']


class PregenerateItemsForm(crispy_forms.CrispyForm):
    num_items = forms.IntegerField(
        label='number of items',
        help_text='Empty text fields will be pregenerated to accommodate this number of items.',
    )
    num_conditions = forms.IntegerField(
        label='number of conditions',
        help_text='Empty text fields will be pregenerated to accommodate this number of conditions.',
)


class ItemUploadForm(crispy_forms.CrispyForm):
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

    def __init__(self, *args, **kwargs):
        self.study= kwargs.pop('study')
        super().__init__(*args, **kwargs)
        if self.study.has_text_items:
            content_help_text = 'Specify which column contains the item text.',
        elif self.study.has_markdown_items:
            content_help_text = 'Specify which column contains the item text formatted with markdown.'
        elif self.study.has_audiolink_items:
            content_help_text = 'Specify which column contains the link to the audio file.',
        self.fields['content_column'].help_text = content_help_text
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

    def clean(self):
        cleaned_data = super().clean()
        data = contrib_csv.read_file(cleaned_data)
        sniff_data = contrib_csv.sniff(data)
        validator_int_columns = ['number_column',]
        delimiter, quoting, has_header = contrib_csv.detect_dialect(sniff_data, cleaned_data, validator_int_columns)
        reader = csv.reader(StringIO(data), delimiter=delimiter, quoting=quoting)
        if has_header:
            next(reader)
        try:
            min_columns = contrib_csv.get_min_columns(cleaned_data)
            for row in reader:
                if not row:
                    continue
                assert len(row) >= min_columns
                int(row[cleaned_data['number_column'] - 1])
                assert row[cleaned_data['condition_column'] - 1]
                assert len(row[cleaned_data['condition_column'] - 1]) < 8
                assert row[cleaned_data['content_column'] - 1]
                if cleaned_data['block_column'] > 0:
                    int(row[cleaned_data['block_column'] - 1])
                for question in self.study.questions:
                    if cleaned_data['question_{}_question_column'.format(question.number + 1)] > 0:
                        assert row[cleaned_data['question_{}_question_column'.format(question.number + 1)] - 1 ]
                    if cleaned_data['question_{}_scale_column'.format(question.number + 1)] > 0:
                        assert row[cleaned_data['question_{}_scale_column'.format(question.number + 1)] - 1]
                        assert len(row[cleaned_data['question_{}_scale_column'.format(question.number + 1)] - 1].split(',')) == \
                               question.scalevalue_set.count()
                    if cleaned_data['question_{}_legend_column'.format(question.number + 1)] > 0:
                        assert row[cleaned_data['question_{}_legend_column'.format(question.number + 1)] - 1]
            contrib_csv.seek_file(cleaned_data)
            self.detected_csv = { 'delimiter': delimiter, 'quoting': quoting, 'has_header': has_header }
        except (ValueError, AssertionError):
            raise forms.ValidationError(
                'File: Unexpected format in line %(n_line)s.',
                code='invalid',
                params={'n_line': reader.line_num})
        return cleaned_data


class ItemQuestionForm(crispy_forms.OptionalLabelMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.append_optional_to_labels()

    class Meta:
        model = models.ItemQuestion
        fields = ['question', 'scale_labels', 'legend']


def itemquestion_factory(n_questions):
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
        Layout(
            Fieldset('Question {{ forloop.counter }}', None, 'question', 'scale_labels', 'legend'),
        ),
    )
    formset_helper.add_input(
        Submit("submit", "Submit"),
    )
    formset_helper.add_input(
        Submit("reset", "Reset"),
    )
    return formset_helper


class ItemListUploadForm(crispy_forms.CrispyForm):
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
                  'Format: Comma separated list of <Item>-<Condition> (e.g. Filler-1a,Exp-2b,...).'
    )

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

    def clean(self):
        cleaned_data = super().clean()
        data = contrib_csv.read_file(cleaned_data)
        sniff_data = contrib_csv.sniff(data)
        validator_int_columns = ['list_column']
        delimiter, quoting, has_header = contrib_csv.detect_dialect(sniff_data, cleaned_data, validator_int_columns)
        reader = csv.reader(StringIO(data), delimiter=delimiter, quoting=quoting)
        if has_header:
            next(reader)
        try:
            used_items = set()
            for row in reader:
                int(row[cleaned_data['list_column'] - 1])
                items_string = row[cleaned_data['items_column'] -1]
                used_items.update(self.read_items(self.experiment, items_string))
            if not len(used_items) == models.Item.objects.filter(experiment=self.experiment).count():
                raise forms.ValidationError('Not all items used in lists.')
            contrib_csv.seek_file(cleaned_data)
            self.detected_csv = { 'delimiter': delimiter, 'quoting': quoting, 'has_header': has_header }
        except (ValueError, AssertionError):
            raise forms.ValidationError(
                'File: Unexpected format in line %(n_line)s.',
                code='invalid',
                params={'n_line': reader.line_num})
        return cleaned_data
