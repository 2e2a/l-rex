import csv
from io import StringIO
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from markdownx.models import MarkdownxFormField
from django import forms
from django.utils.html import strip_tags


from . import csv as contrib_csv


def disable_form_field(form, field):
    form.fields[field].widget.attrs['readonly'] = True
    form.fields[field].widget.attrs['disabled'] = True
    form.fields[field].disabled = True


class OptionalLabelMixin:
    optional_label_ignore_fields = None

    def append_optional_to_labels(self):
        for name, field in self.fields.items():
            if (
                    not field.required
                    and (not self.optional_label_ignore_fields or not name in self.optional_label_ignore_fields)
                    and not isinstance(field.widget, forms.widgets.CheckboxInput)
            ):
                field.label = '{} (optional)'.format(field.label)


class PrimarySubmit(Submit):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_classes = 'btn btn-outline-primary'


class DangerSubmit(Submit):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_classes = 'btn btn-outline-danger'


class SecondarySubmit(Submit):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_classes = 'btn btn-outline-secondary'


class HelperMixin:
    helper = None
    submit_label = None
    submit_danger = False
    save_label = None

    add_save = False

    def __init__(self, *args, **kwargs):
        self.add_save = kwargs.pop('add_save', False)
        super().__init__(*args, **kwargs)

    def init_helper(self):
        self.helper = FormHelper()
        if self.submit_danger:
            self.helper.add_input(DangerSubmit('submit', self.submit_label))
        else:
            self.helper.add_input(PrimarySubmit('submit', self.submit_label))
        if self.add_save:
            self.helper.add_input(SecondarySubmit('save', self.save_label))


class StripTagsInMarkdownMixin:

    def clean(self):
        data = super().clean()
        for field in data:
            if isinstance(self.fields[field], MarkdownxFormField):
                data[field] = strip_tags(data[field])
        return data


class CrispyForm(OptionalLabelMixin, HelperMixin, StripTagsInMarkdownMixin, forms.Form):
    submit_label = 'Submit'
    save_label = 'Save'

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study', None)
        super().__init__(*args, **kwargs)
        self.init_helper()
        self.append_optional_to_labels()


class CrispyModelForm(OptionalLabelMixin, HelperMixin, StripTagsInMarkdownMixin, forms.ModelForm):
    submit_label = 'Submit'
    save_label = 'Save'

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study', None)
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


class CrispyModelFormsetFactory:
    form_tag = True

    def __new__(cls, form_count=None, custom_formset=None, study=None):
        helper = FormHelper()
        helper.form_tag = cls.form_tag
        layout = cls.get_layout(study)
        if layout:
            helper.add_layout(layout)
        if cls.form_tag:
            inputs = cls.get_inputs(study=study)
            if inputs is None:
                helper.add_input(PrimarySubmit('submit', 'Submit'))
                helper.add_input(SecondarySubmit('save', 'Save'))
                if form_count:
                    helper.add_input(SecondarySubmit('reset', 'Reset'))
            else:
                for input in inputs:
                    helper.add_input(input)
        factory_kwargs = {
            'form': cls.form,
        }
        if form_count:
            factory_kwargs.update({
                'extra': 0,
                'min_num': form_count,
            })
        else:
            form_disabled = study.is_active or study.is_finished
            factory_kwargs.update({
                'extra': 1 if not form_disabled else 0,
                'can_delete': True
            })
        if custom_formset:
            factory_kwargs['formset'] = custom_formset
        formset_class = forms.modelformset_factory(cls.model, **factory_kwargs)
        formset_class.helper = helper
        return formset_class

    @staticmethod
    def get_inputs(study=None):
        return None

    @staticmethod
    def get_layout(study=None):
        return None
