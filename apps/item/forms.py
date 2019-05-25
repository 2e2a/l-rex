import csv
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


# TODO: ItemUploadForm
class UploadItemsForm(crispy_forms.CrispyForm):
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
                assert int(row[cleaned_data['number_column'] - 1])
                assert row[cleaned_data['condition_column'] - 1]
                assert len(row[cleaned_data['condition_column'] - 1]) < 8
                assert row[cleaned_data['content_column'] - 1]
                if cleaned_data['block_column'] > 0:
                    assert int(row[cleaned_data['block_column'] - 1])
                for question in self.study.questions:
                    if cleaned_data['question_{}_question_column'.format(question.number)] > 0:
                        assert row[cleaned_data['question_{}_question_column'.format(question.number)] - 1 ]
                    if cleaned_data['question_{}_scale_column'.format(question.number)] > 0:
                        assert row[cleaned_data['question_{}_scale_column'.format(question.number)] - 1]
                        assert len(row[cleaned_data['question_{}_scale_column'.format(question.number)] - 1].split(',')) == \
                               question.scalevalue_set.count()
                    if cleaned_data['question_{}_legend_column'.format(question.number)] > 0:
                        assert row[cleaned_data['question_{}_legend_column'.format(question.number)] - 1]
            contrib_csv.seek_file(cleaned_data)
            self.detected_csv = {
                'delimiter': delimiter,
                'quoting': quoting,
                'has_header': has_header,
            }
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


def itemquestion_factory(n_questions, n_item_questions=0):
    extra = (n_questions - n_item_questions) if n_questions > n_item_questions else 0
    return modelformset_factory(
        models.ItemQuestion,
        form=ItemQuestionForm,
        max_num=n_questions,
        extra=extra,
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
            scale_labels = [scale_value.label for scale_value in question.scalevalue_set.all()]
            form['scale_labels'].initial = ','.join(scale_labels)
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


class UploadItemListForm(crispy_forms.CrispyForm):
    file = forms.FileField(
        help_text='The CSV file must contain a column for the item list number, item number and condition.'
                  'Valid column delimiters: colon, semicolon, comma, space, or tab.',
    )
    list_column = forms.IntegerField(
        initial=1,
        help_text='Specify which column contains the item list number.',
    )
    item_number_column = forms.IntegerField(
        initial=2,
        help_text='Specify which column contains the item number.',
    )
    item_condition_column = forms.IntegerField(
        initial=3,
        help_text='Specify which column contains the condition.',
    )

    def __init__(self, *args, **kwargs):
        self.experiment = kwargs.pop('experiment')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        data = contrib_csv.read_file(cleaned_data)
        sniff_data = contrib_csv.sniff(data)
        validator_int_columns = ['list_column', 'item_number_column']
        delimiter, quoting, has_header = contrib_csv.detect_dialect(sniff_data, cleaned_data, validator_int_columns)
        reader = csv.reader(StringIO(data), delimiter=delimiter, quoting=quoting)
        if has_header:
            next(reader)
        try:
            item_count = 0
            for row in reader:
                assert int(row[cleaned_data['list_column'] - 1])
                assert int(row[cleaned_data['item_number_column'] - 1])
                item_number = row[cleaned_data['item_number_column'] - 1]
                item_condition = row[cleaned_data['item_condition_column'] -1]
                if not self.experiment.item_set.filter(number=item_number, condition=item_condition).exists():
                    error = 'Item {}{} is not defined.'.format(item_number, item_condition)
                    raise forms.ValidationError(error)
                item_count += 1
            if not item_count == self.experiment.item_set.count():
                raise forms.ValidationError('Not all items used in lists.')
            contrib_csv.seek_file(cleaned_data)
        except (ValueError, AssertionError):
            raise forms.ValidationError(
                'File: Unexpected format in line %(n_line)s.',
                code='invalid',
                params={'n_line': reader.line_num})
        return cleaned_data
