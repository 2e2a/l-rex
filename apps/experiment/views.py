from django.views.generic import DetailView
from django.views.generic import ListView

from . import models


class SetupDetailView(DetailView):
    model = models.Setup


class ExperimentDetailView(DetailView):
    model = models.Experiment


class ListListView(ListView):
    model = models.ListItem
