from apps.contrib import forms as crispy_forms

from . import models


class ExperimentForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.Experiment
        fields = ['title', 'is_filler']
