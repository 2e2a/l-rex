from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms


class OptionalLabelMixin:
    optional_label_ignore_fields = None

    def append_optional_to_labels(self):
        for name, field in self.fields.items():
            if not field.required \
                    and (not self.optional_label_ignore_fields or not name in self.optional_label_ignore_fields) \
                    and not isinstance(field.widget, forms.widgets.CheckboxInput):
                field.label = '{} (optional)'.format(field.label)


class CrispyForm(OptionalLabelMixin, forms.Form):
    submit_label = 'Submit'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = self.custom_helper if hasattr(self, 'custom_helper') else FormHelper()
        self.helper.add_input(Submit('submit', self.submit_label))
        self.append_optional_to_labels()



class CrispyModelForm(OptionalLabelMixin, forms.ModelForm):
    submit_label = 'Submit'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = self.custom_helper if hasattr(self, 'custom_helper') else FormHelper()
        self.helper.add_input(Submit('submit', self.submit_label))
        self.append_optional_to_labels()
