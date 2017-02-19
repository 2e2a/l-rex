from django.views.generic import DetailView

from . import models


class ExperimentDetailView(DetailView):
    model = models.Experiment
