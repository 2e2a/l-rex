from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms


class CrispyForm(forms.Form):
    submit_label = 'Submit'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', self.submit_label))


class CrispyModelForm(forms.ModelForm):
    submit_label = 'Submit'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', self.submit_label))
