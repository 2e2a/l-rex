import re
import csv
from io import StringIO
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms


from . import csv as contrib_csv
from . import utils


def disable_form_field(form, field):
    form.fields[field].widget.attrs['readonly'] = True
    form.fields[field].widget.attrs['disabled'] = True
    form.fields[field].disabled = True


class OptionalLabelMixin:
    optional_label_ignore_fields = None

    def append_optional_to_labels(self):
        for name, field in self.fields.items():
            if not field.required \
                    and (not self.optional_label_ignore_fields or not name in self.optional_label_ignore_fields) \
                    and not isinstance(field.widget, forms.widgets.CheckboxInput):
                field.label = '{} (optional)'.format(field.label)


class HelperMixin:
    helper = None
    submit_label = None
    save_label = None

    add_save = False

    def __init__(self, *args, **kwargs):
        self.add_save = kwargs.pop('add_save', False)
        super().__init__(*args, **kwargs)

    def init_helper(self):
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', self.submit_label))
        if self.add_save:
            self.helper.add_input(Submit('save', self.save_label, css_class='btn-secondary'))


class ListField(forms.CharField):

    def validate(self, value):
        super().validate(value)
        value_list = utils.split_list_string(value)
        if not len(value_list) > 1:
            raise forms.ValidationError('At least two values must be entered.')


class CrispyForm(OptionalLabelMixin, HelperMixin, forms.Form):
    submit_label = 'Submit'
    save_label = 'Save'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_helper()
        self.append_optional_to_labels()


class CrispyModelForm(OptionalLabelMixin, HelperMixin, forms.ModelForm):
    submit_label = 'Submit'
    save_label = 'Save'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_helper()
        self.append_optional_to_labels()


class CSVUploadForm(CrispyForm):
    file = forms.FileField(
        help_text='The CSV file.',
        widget=forms.FileInput,
    )
    delimiter = forms.CharField(
        label='CSV delimiter',
        max_length=2,
        required=False,
        help_text='If the upload fails with CSV errors, try setting the delimiter character used in your CSV to '
                  'separate the columns.',
    )

    validator_int_columns = None
    detected_csv = None

    def check_upload_form(self, reader, cleaned_data):
        raise NotImplementedError

    def clean(self):
        cleaned_data = super().clean()
        if 'file' in cleaned_data:
            data = contrib_csv.read_file(cleaned_data)
            delimiter = cleaned_data['delimiter']
            sniff_data = contrib_csv.sniff(data)
            delimiter, quoting, has_header = contrib_csv.detect_dialect(
                sniff_data, cleaned_data, self.validator_int_columns, user_delimiter=delimiter
            )
            self.detected_csv = {'delimiter': delimiter, 'quoting': quoting, 'has_header': has_header}
            contrib_csv.seek_file(cleaned_data)
            data = contrib_csv.read_file(cleaned_data)
            reader = csv.reader(
                StringIO(data), delimiter=self.detected_csv['delimiter'], quoting=self.detected_csv['quoting'])
            if self.detected_csv['has_header']:
                next(reader)
            try:
                self.check_upload_form(reader, cleaned_data)
                contrib_csv.seek_file(cleaned_data)
            except forms.ValidationError as error:
                raise forms.ValidationError('Line {}: {}'.format(reader.line_num, str(error.message)), code='invalid')
            except (ValueError, AssertionError):
                raise forms.ValidationError('Line {}: unexpected entry.'.format(reader.line_num), code='invalid')
        return cleaned_data
