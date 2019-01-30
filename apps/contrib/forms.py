from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms


class OptionalLabelMixin:

    def append_optional_to_labels(self):
        for field in self.fields.values():
            if not field.required and not isinstance(field.widget, forms.widgets.CheckboxInput):
                field.label = '{} (optional)'.format(field.label)


class CrispyForm(OptionalLabelMixin, forms.Form):
    submit_label = 'Submit'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', self.submit_label))
        self.append_optional_to_labels()




class CrispyModelForm(OptionalLabelMixin, forms.ModelForm):
    submit_label = 'Submit'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', self.submit_label))
        self.append_optional_to_labels()
