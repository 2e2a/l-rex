from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from . import models


class SetupDetailView(LoginRequiredMixin, generic.DetailView):
    model = models.Setup
    title = 'Experiment Setup'


class SetupCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Setup
    fields = ['title']
    title = 'Create Experiment Setup'

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


class SetupListView(LoginRequiredMixin, generic.ListView):
    model = models.Setup
    title = 'Your Experiment Setups'

    def get_queryset(self):
        return super().get_queryset().filter(creator=self.request.user)
