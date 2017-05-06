from django.views import generic

from . import models


class SetupDetailView(generic.DetailView):
    model = models.Setup
    title = 'Experiment Setup'


class SetupCreateView(generic.CreateView):
    model = models.Setup
    fields = ['title']
    title = 'Create Experiment Setup'

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)

