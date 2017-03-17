from django.views import generic

from . import models


class SetupDetailView(generic.DetailView):
    model = models.Setup


class SetupCreateView(generic.CreateView):
    model = models.Setup
    fields = ['title']

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


class ExperimentDetailView(generic.DetailView):
    model = models.Experiment


class ExperimentCreateView(generic.CreateView):
    model = models.Experiment
    fields = ['title', 'item_type']

    def dispatch(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        self.setup = models.Setup.objects.get(slug=setup_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.setup = self.setup
        return super().form_valid(form)

class ListListView(generic.ListView):
    model = models.ListItem
