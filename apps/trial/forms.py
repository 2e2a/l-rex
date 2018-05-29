from django import forms

from apps.contrib import forms as crispy_forms
from apps.study import models as study_models

from . import models


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
        if self.study.allow_anonymous:
            self.fields['id'].widget = forms.HiddenInput()
        else :
            self.fields['id'].required = True

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['password'] != self.study.password:
            raise forms.ValidationError('Invalid password.')
        return cleaned_data


class RatingForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.Rating
        fields = ['scale_value']

    def __init__(self, *args, **kwargs):
        study = kwargs.pop('study')
        super().__init__(*args, **kwargs)
        self.fields['scale_value'].empty_label = None
        self.fields['scale_value'].queryset = study_models.ScaleValue.objects.filter(study=study)
