from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit
from django.forms import ModelForm, BooleanField
from django.forms import modelformset_factory

from .models import Response


class ResponseForm(ModelForm):
    delete = BooleanField(required=False)

    class Meta:
        model = Response
        fields = ['label', 'delete']


class ResponseFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.render_unmentioned_fields = True


responseformset_factory = modelformset_factory(Response, form=ResponseForm, min_num=1, extra=1)

response_formset_helper = ResponseFormSetHelper()
response_formset_helper.add_layout(
    Layout(
        Fieldset('Response {{ forloop.counter }}'),
    ),
)
response_formset_helper.add_input(
    Submit("submit", "Save"),
)
