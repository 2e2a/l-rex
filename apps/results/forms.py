from django import forms

from apps.study import models as study_models
from . import models


class UserResponseForm(forms.ModelForm):

    class Meta:
        model = models.UserResponse
        fields = ['scale_value']

    def __init__(self, *args, **kwargs):
        study = kwargs.pop('study')
        super().__init__(*args, **kwargs)
        self.fields['scale_value'].empty_label = None
        self.fields['scale_value'].queryset = study_models.ScaleValue.objects.filter(study=study)

