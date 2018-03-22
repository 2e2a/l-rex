from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit
from django.forms import ModelForm, BooleanField
from django.forms import modelformset_factory

from .models import ScaleValue


class ScaleValueForm(ModelForm):
    delete = BooleanField(required=False)

    class Meta:
        model = ScaleValue
        fields = ['label', 'delete']


class ScaleFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.render_unmentioned_fields = True


scaleformset_factory = modelformset_factory(ScaleValue, form=ScaleValueForm, min_num=1, extra=1)

scale_formset_helper = ScaleFormSetHelper()
scale_formset_helper.add_layout(
    Layout(
        Fieldset('Scale Value {{ forloop.counter }}'),
    ),
)
scale_formset_helper.add_input(
    Submit("submit", "Save"),
)
