from django import forms

from apps.contrib import forms as crispy_forms

from . import models


class ExperimentForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.Experiment
        fields = [
            'title',
            'is_filler',
            'is_example'
        ]

    def __init__(self, *args, **kwargs):
        study = kwargs.pop('study')
        super().__init__(*args, **kwargs)
        if not study.use_blocks:
            self.fields['is_example'].widget = forms.HiddenInput()
