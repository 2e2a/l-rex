import csv
from io import StringIO
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
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
    num_items = forms.IntegerField()
    num_conditions = forms.IntegerField()


class UploadItemsForm(crispy_forms.CrispyForm):
    file = forms.FileField()
    number_column = forms.IntegerField(initial=1)
    condition_column = forms.IntegerField(initial=2)
    text_column = forms.IntegerField(initial=3)

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data['file']
        try:
            data = file.read().decode()
            dialect = csv.Sniffer().sniff(data[:128])
            reader = csv.reader(StringIO(data), dialect)
            try:
                for row in reader:
                    assert len(row) >= cleaned_data['number_column']
                    assert len(row) >= cleaned_data['condition_column']
                    assert len(row) >= cleaned_data['text_column']
                    assert int(row[cleaned_data['number_column'] - 1])
                    assert row[cleaned_data['condition_column'] - 1]
                    assert row[cleaned_data['text_column'] - 1]
            except AssertionError:
                raise forms.ValidationError(
                    'File: Unexpected format in line %(n_line)s.',
                    code='invalid',
                    params={'n_line': reader.line_num})
        except csv.Error:
            raise forms.ValidationError('Unsupported CSV format.')
        file.seek(0)
        return cleaned_data
