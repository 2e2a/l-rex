from django import forms

from apps.contrib import forms as crispy_forms

from . import models


class ExperimentForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.Experiment
        fields = [
            'title',
            'is_filler',
            'is_example',
            'block',
        ]

    def __init__(self, *args, **kwargs):
        study = kwargs.pop('study')
        disable_block_settings= kwargs.pop('disable_block_settings')
        super().__init__(*args, **kwargs)
        if not study.use_blocks:
            self.fields['is_example'].widget = forms.HiddenInput()
            self.fields['block'].widget = forms.HiddenInput()
        if disable_block_settings:
            self.fields['is_example'].widget.attrs['readonly'] = True
            self.fields['is_example'].widget.attrs['disabled'] = True
            self.fields['block'].widget.attrs['readonly'] = True
            self.fields['block'].widget.attrs['disabled'] = True
