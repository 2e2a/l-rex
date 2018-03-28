import csv
from io import StringIO
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms


class PregenerateItemsForm(forms.Form):
    num_items = forms.IntegerField()
    num_conditions = forms.IntegerField()


class UploadTextItemsForm(forms.Form):
    file = forms.FileField()
    number_column = forms.IntegerField(initial=1)
    condition_column = forms.IntegerField(initial=2)
    text_column = forms.IntegerField(initial=3)

    def __init__(self, *args, **kwargs):
        # TODO: Add default form helper (and template)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Submit'))

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
