from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit
from django import forms

from apps.contrib import forms as crispy_forms
from apps.study import models as study_models

from . import models


class QuestionnaireBlockForm(forms.ModelForm):

    class Meta:
        model = models.QuestionnaireBlock
        fields = ['randomization']


def questionnaire_block_factory(n_blocks):
    return forms.modelformset_factory(
        models.QuestionnaireBlock,
        form=QuestionnaireBlockForm,
        min_num=n_blocks,
        max_num=n_blocks,
    )


questionnaire_block_formset_helper = FormHelper()
questionnaire_block_formset_helper.add_layout(
    Layout(
        Fieldset('Item block {{ forloop.counter }}', None, 'instructions', 'randomization'),
    ),
)
questionnaire_block_formset_helper.add_input(
    Submit("submit", "Submit"),
)


class QuestionnaireBlockUpdateForm(forms.ModelForm):

    class Meta:
        model = models.QuestionnaireBlock
        fields = ['instructions']


def questionnaire_block_update_factory(n_blocks):
    return forms.modelformset_factory(
        models.QuestionnaireBlock,
        form=QuestionnaireBlockUpdateForm,
        min_num=n_blocks,
        max_num=n_blocks,
    )


questionnaire_block_update_formset_helper = FormHelper()
questionnaire_block_update_formset_helper.add_layout(
    Layout(
        Fieldset('Item block {{ forloop.counter }}', None, 'instructions'),
    ),
)
questionnaire_block_update_formset_helper.add_input(
    Submit("submit", "Submit"),
)


class TrialForm(crispy_forms.CrispyModelForm):
    password = forms.CharField(
        max_length=200,
        widget=forms.PasswordInput,
        help_text='Provide a password (as instructed by the experimenter).',
    )

    class Meta:
        model = models.Trial
        fields = ['id']

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study')
        super().__init__(*args, **kwargs)
        if self.study.require_participant_id:
            self.fields['id'].required = True
        else :
            self.fields['id'].widget = forms.HiddenInput()

    def clean_password(self):
        password = self.cleaned_data['password']
        if password != self.study.password:
            raise forms.ValidationError('Invalid password.')
        return password


class RatingForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.Rating
        fields = ['scale_value']

    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question')
        item_question = kwargs.pop('item_question', None)
        super().__init__(*args, **kwargs)
        self.fields['scale_value'].empty_label = None
        self.fields['scale_value'].queryset = study_models.ScaleValue.objects.filter(question=question)
        if item_question and item_question.scale_labels:
            custom_choices = []
            for (pk, _ ), custom_label \
                    in zip(self.fields['scale_value'].choices, item_question.scale_labels.split(',')):
                custom_choices.append((pk, custom_label))
            self.fields['scale_value'].choices = custom_choices



class RatingFormsetForm(forms.ModelForm):

    class Meta:
        model = models.Rating
        fields = ['scale_value']
        widgets = {
            'scale_value': forms.RadioSelect(
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['scale_value'].empty_label = None
        self.fields['scale_value'].required = False


def ratingformset_factory(n_questions=1):
    return forms.modelformset_factory(
        models.Rating,
        form=RatingFormsetForm,
        min_num=n_questions,
        max_num=n_questions,
        extra=0,
        validate_max=True,
    )

def customize_to_questions(ratingformset, questions, item_questions):
    for i, (question, form) in enumerate(zip(questions, ratingformset)):
        scale_value = form.fields.get('scale_value')
        scale_value.queryset = scale_value.queryset.filter(question=question)
        scale_value.label = \
            item_questions[i].question if item_questions else question.question
        scale_value.help_text = \
            item_questions[i].legend if item_questions and item_questions[i].legend else question.legend
        if item_questions and item_questions[i].scale_labels:
            custom_choices = []
            for (pk, _ ), custom_label in zip(scale_value.choices, item_questions[i].scale_labels.split(',')):
                custom_choices.append((pk, custom_label))
            scale_value.choices = custom_choices


class RatingFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

rating_formset_helper = RatingFormSetHelper()
rating_formset_helper.add_input(
    Submit("submit", "Submit"),
)
