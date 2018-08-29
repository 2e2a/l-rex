from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit
from django.forms import ModelForm, BooleanField
from django.forms import modelformset_factory

from apps.contrib import forms as crispy_forms

from . import models


class StudyForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.Study
        fields = [
            'title',
            'item_type',
            'rating_instructions',
            'require_participant_id',
            'password',
            'end_date',
            'trial_limit'
        ]


class QuestionForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.Question
        fields = [
            'question',
            'legend',
        ]


class ScaleValueForm(ModelForm):
    delete = BooleanField(required=False)

    class Meta:
        model = models.ScaleValue
        fields = ['label', 'delete']


def scaleformset_factory(extra=0):
    return modelformset_factory(models.ScaleValue, form=ScaleValueForm, min_num=1, extra=extra)


class ScaleFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.render_unmentioned_fields = True


scale_formset_helper = ScaleFormSetHelper()
scale_formset_helper.add_layout(
    Layout(
        Fieldset('Scale value {{ forloop.counter }}'),
    ),
)
scale_formset_helper.add_input(
    Submit("add", "Add"),
)
scale_formset_helper.add_input(
    Submit("submit", "Submit"),
)
