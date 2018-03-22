from django import forms

from apps.study import models as study_models

from . import models


class TrialForm(forms.ModelForm):
    password = forms.CharField(max_length=200, widget=forms.PasswordInput)

    class Meta:
        model = models.Trial
        fields = ['id']

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study')
        super().__init__(*args, **kwargs)
        self.fields['id'].required = not self.study.allow_anonymous

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['password'] != self.study.password:
            raise forms.ValidationError('Invalid password.')
        return cleaned_data


class RatingForm(forms.ModelForm):

    class Meta:
        model = models.Rating
        fields = ['scale_value']

    def __init__(self, *args, **kwargs):
        study = kwargs.pop('study')
        super().__init__(*args, **kwargs)
        self.fields['scale_value'].empty_label = None
        self.fields['scale_value'].queryset = study_models.ScaleValue.objects.filter(study=study)
