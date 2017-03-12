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


class ListListView(generic.ListView):
    model = models.ListItem
