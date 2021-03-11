from django import forms

from apps.contrib import forms as contrib_forms

from . import models


class MaterialsForm(contrib_forms.CrispyModelForm):

    class Meta:
        model = models.Materials
        fields = [
            'title',
            'item_list_distribution',
            'is_filler',
            'is_example',
            'block',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.study.use_blocks:
            self.fields['is_example'].widget = forms.HiddenInput()
            self.fields['block'].widget = forms.HiddenInput()


class MaterialsSettingsForm(MaterialsForm):

    def __init__(self, *args, **kwargs):
        disable_block_settings = kwargs.pop('disable_block_settings')
        disable_list_settings = kwargs.pop('disable_list_settings')
        super().__init__(*args, **kwargs)
        if disable_list_settings:
            contrib_forms.disable_form_field(self, 'item_list_distribution')
        if disable_block_settings:
            contrib_forms.disable_form_field(self, 'is_example')
            contrib_forms.disable_form_field(self, 'block')
