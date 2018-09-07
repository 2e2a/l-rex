from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit
from django import forms

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
    scale_labels = forms.CharField(
        max_length=200,
        required=True,
        help_text='TODO, comma separated'
    )

    class Meta:
        model = models.Question
        fields = [
            'question',
            'scale_labels',
            'legend',
        ]

    def clean_scale_labels(self):
        scale_labels = self.cleaned_data['scale_labels']
        if scale_labels and len(scale_labels.split(','))<2:
            raise forms.ValidationError('At least two scale values need to be defined')
        return scale_labels

def question_formset_factory(n_questions, extra=0):
    return forms.modelformset_factory(
        models.Question,
        form=QuestionForm,
        min_num=n_questions,
        extra=extra,
    )

def initialize_with_questions(question_formset, questions):
    for question, form in zip(questions, question_formset):
        form['scale_labels'].initial = ','.join([scale_value.label for scale_value in question.scalevalue_set.all()])

question_formset_helper = FormHelper()
question_formset_helper.add_layout(
    Layout(
        Fieldset('Question {{ forloop.counter }}', None, 'question', 'scale_labels', 'legend'),
    ),
)
question_formset_helper.add_input(
    Submit("add", "Add"),
)
question_formset_helper.add_input(
    Submit("delete", "Delete last"),
)
question_formset_helper.add_input(
    Submit("submit", "Submit"),
)
