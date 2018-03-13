from django import forms

from apps.study import models as study_models
from . import models


class UserResponseForm(forms.ModelForm):

    class Meta:
        model = models.UserResponse
        fields = ['response']

    def __init__(self, *args, **kwargs):
        study = kwargs.pop('study')
        super().__init__(*args, **kwargs)
        self.fields['response'].empty_label = None
        self.fields['response'].queryset = study_models.Response.objects.filter(study=study)

