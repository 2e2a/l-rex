import csv
from io import StringIO
from django import forms

from apps.contrib import forms as crispy_forms

from . import models


class TextItemForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.TextItem
        fields = ['number', 'condition', 'text']


class AudioLinkItemForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.AudioLinkItem
        fields = ['number', 'condition', 'url']


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

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data['file']
        try:
            data = file.read().decode()
            dialect = csv.Sniffer().sniff(data[:128])
            has_header = csv.Sniffer().has_header(data[:128])
            reader = csv.reader(StringIO(data), dialect)
            if has_header:
                next(reader)
            try:
                for row in reader:
                    assert len(row) >= cleaned_data['number_column']
                    assert len(row) >= cleaned_data['condition_column']
                    assert len(row) >= cleaned_data['text_column']
                    assert int(row[cleaned_data['number_column'] - 1])
                    assert row[cleaned_data['condition_column'] - 1]
                    assert row[cleaned_data['text_column'] - 1]
            except (ValueError, AssertionError):
                raise forms.ValidationError(
                    'File: Unexpected format in line %(n_line)s.',
                    code='invalid',
                    params={'n_line': reader.line_num})
        except csv.Error:
            raise forms.ValidationError('Unsupported CSV format.')
        file.seek(0)
        return cleaned_data
