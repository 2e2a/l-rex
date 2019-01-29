import csv
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit
from django import forms
from django.forms import modelformset_factory
from io import StringIO

from apps.contrib import forms as crispy_forms

from . import models


class TextItemForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.TextItem
        fields = ['number', 'condition', 'text', 'block']


class AudioLinkItemForm(crispy_forms.CrispyModelForm):

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
    text_column = forms.IntegerField(
        initial=3,
        help_text='Specify which column contains the text or the link to the audio file.',
    )
    block_column = forms.IntegerField(
        initial=0,
        help_text='Optional: specify which column contains the questionnaire block. '
                  'Set to 0 if the questionnaire does not contain more than one block.',
    )

    def __init__(self, *args, **kwargs):
        self.questions = kwargs.pop('questions')
        super().__init__(*args, **kwargs)
        for i, _ in enumerate(self.questions):
            self.fields.update(
                {
                    'question_{}_question_column'.format(i+1):
                    forms.IntegerField(
                        initial=0,
                        help_text='Optional: specify which column contains the item-specific question. '
                                  'Set to 0 to use the default question as specified in the study settings.'
                     )
                }
            )
            self.fields.update(
                {
                    'question_{}_scale_column'.format(i+1):
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
                    'question_{}_legend_column'.format(i+1):
                        forms.IntegerField(
                            initial=0,
                            help_text='Optional: specify which column contains the items-specific scale legend. '
                                      'Set to 0 to use the default legend as specified in the study settings.'
                        )
                }
            )

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data['file']
        try:
            try:
                data = file.read().decode('utf-8')
            except UnicodeDecodeError:
                file.seek(0)
                data = file.read().decode('latin-1')
            data_len = len(data)
            sniff_data = data[:500 if data_len > 500 else data_len]
            dialect = csv.Sniffer().sniff(sniff_data)
            has_header = csv.Sniffer().has_header(sniff_data)
            reader = csv.reader(StringIO(data), dialect)
            if has_header:
                next(reader)
            try:
                for row in reader:
                    assert len(row) >= cleaned_data['number_column']
                    assert len(row) >= cleaned_data['condition_column']
                    assert len(row) >= cleaned_data['text_column']
                    assert len(row) >= cleaned_data['block_column']
                    for i, _ in enumerate(self.questions):
                        if cleaned_data['question_{}_question_column'.format(i+1)] > 0:
                            assert len(row) >= cleaned_data['question_{}_question_column'.format(i+1)]
                        if cleaned_data['question_{}_scale_column'.format(i+1)] > 0:
                            assert len(row) >= cleaned_data['question_{}_scale_column'.format(i+1)]
                        if cleaned_data['question_{}_legend_column'.format(i+1)] > 0:
                            assert len(row) >= cleaned_data['question_{}_legend_column'.format(i+1)]

                    assert int(row[cleaned_data['number_column'] - 1])
                    assert row[cleaned_data['condition_column'] - 1]
                    assert row[cleaned_data['text_column'] - 1]
                    if cleaned_data['block_column'] > 0:
                        assert int(row[cleaned_data['block_column'] - 1])
                    for i, question in enumerate(self.questions):
                        if cleaned_data['question_{}_question_column'.format(i+1)] > 0:
                            assert row[cleaned_data['question_{}_question_column'.format(i+1)] - 1 ]
                        if cleaned_data['question_{}_scale_column'.format(i+1)] > 0:
                            assert row[cleaned_data['question_{}_scale_column'.format(i+1)] - 1]
                            assert len(row[cleaned_data['question_{}_scale_column'.format(i+1)] - 1].split(',')) == \
                                   question.scalevalue_set.count()
                        if cleaned_data['question_{}_legend_column'.format(i+1)] > 0:
                            assert row[cleaned_data['question_{}_legend_column'.format(i+1)] - 1]
            except (ValueError, AssertionError):
                raise forms.ValidationError(
                    'File: Unexpected format in line %(n_line)s.',
                    code='invalid',
                    params={'n_line': reader.line_num})
        except (UnicodeDecodeError, TypeError):
            raise forms.ValidationError('Unsupported file encoding. Use UTF-8 or Latin-1.')
        except csv.Error:
            raise forms.ValidationError('Unsupported CSV format.')
        file.seek(0)
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
    for question, form in zip(questions, itemquestion_formset):
        if not form['question'].initial:
            form['question'].initial = question.question
            scale_labels = [scale_value.label for scale_value in question.scalevalue_set.all()]
            form['scale_labels'].initial = ','.join(scale_labels)
            form['legend'].initial = question.legend


itemquestion_formset_helper = FormHelper()
itemquestion_formset_helper.add_layout(
    Layout(
        Fieldset('Question {{ forloop.counter }}', None, 'question', 'scale_labels', 'legend'),
    ),
)
itemquestion_formset_helper.add_input(
    Submit("submit", "Submit"),
)
itemquestion_formset_helper.add_input(
    Submit("reset", "Reset"),
)


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
        file = cleaned_data['file']
        try:
            try:
                data = file.read().decode('utf-8')
            except UnicodeDecodeError:
                file.seek(0)
                data = file.read().decode('latin-1')
            data_len = len(data)
            sniff_data = data[:16 if data_len > 16 else data_len]
            dialect = csv.Sniffer().sniff(sniff_data)
            has_header = csv.Sniffer().has_header(sniff_data)
            reader = csv.reader(StringIO(data), dialect)
            if has_header:
                next(reader)
            try:
                item_count = 0
                for row in reader:
                    assert len(row) >= cleaned_data['list_column']
                    assert len(row) >= cleaned_data['item_number_column']
                    assert len(row) >= cleaned_data['item_condition_column']
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
            except (ValueError, AssertionError):
                raise forms.ValidationError(
                    'File: Unexpected format in line %(n_line)s.',
                    code='invalid',
                    params={'n_line': reader.line_num})
        except (UnicodeDecodeError, TypeError):
            raise forms.ValidationError('Unsupported file encoding. Use UTF-8 or Latin-1.')
        except csv.Error:
            raise forms.ValidationError('Unsupported CSV format.')
        file.seek(0)
        return cleaned_data
