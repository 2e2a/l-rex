from django.views import generic

from apps.setup import models as setup_models

from . import models


class ExperimentDetailView(generic.DetailView):
    model = models.Experiment


class ExperimentCreateView(generic.CreateView):
    model = models.Experiment
    fields = ['title', 'item_type']

    def dispatch(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        self.setup = setup_models.Setup.objects.get(slug=setup_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.setup = self.setup
        return super().form_valid(form)
