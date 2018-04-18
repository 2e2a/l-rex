from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit
from django.forms import ModelForm, BooleanField
from django.forms import modelformset_factory

from apps.contrib import forms as crispy_forms

from . import models


class StudyForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.Study
        fields = ['title', 'rating_instructions', 'rating_question', 'rating_legend', 'end_date', 'trial_limit',
                  'password', 'allow_anonymous']


class ScaleValueForm(ModelForm):
    delete = BooleanField(required=False)

    class Meta:
        model = models.ScaleValue
        fields = ['label', 'delete']


class ScaleFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.render_unmentioned_fields = True


scaleformset_factory = modelformset_factory(models.ScaleValue, form=ScaleValueForm, min_num=1, extra=1)

scale_formset_helper = ScaleFormSetHelper()
scale_formset_helper.add_layout(
    Layout(
        Fieldset('Scale Value {{ forloop.counter }}'),
    ),
)
scale_formset_helper.add_input(
    Submit("submit", "Submit"),
)
