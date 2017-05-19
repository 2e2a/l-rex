from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from apps.setup import models as setup_models

from . import models


class ExperimentDetailView(LoginRequiredMixin, generic.DetailView):
    model = models.Experiment
    title = 'Experiment Overview'


class ExperimentCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Experiment
    fields = ['title', 'item_type']
    title = 'Create Experiment'

    def dispatch(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        self.setup = setup_models.Setup.objects.get(slug=setup_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.setup = self.setup
        return super().form_valid(form)
