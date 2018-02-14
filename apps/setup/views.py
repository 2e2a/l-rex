from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import generic

from . import models


class SetupDetailView(LoginRequiredMixin, generic.DetailView):
    model = models.Setup
    title = 'Experiment Setup'

    @property
    def breadcrumbs(self):
        return [
            (self.setup.title, ''),
        ]

    @property
    def setup(self):
        return self.object


class SetupRunView(LoginRequiredMixin, generic.DetailView):
    model = models.Setup
    title = 'Run Experiment Setup'
    template_name = 'lrex_setup/setup_run.html'

    @property
    def breadcrumbs(self):
        return [
            (self.setup.title, ''),
        ]

    @property
    def setup(self):
        return self.object


class SetupCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Setup
    fields = ['title', 'item_type']
    title = 'Create Experiment Setup'

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)

class SetupUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = models.Setup
    fields = ['title', 'item_type']
    title = 'Edit Experiment Setup'

    @property
    def breadcrumbs(self):
        return [
            (self.object.title, reverse('setup', args=[self.object.slug])),
            ('settings', ''),
        ]


class SetupDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = models.Setup
    title = 'Delete Experiment Setup'
    message = 'Delete Setup?'

    @property
    def breadcrumbs(self):
        return [
            (self.object.title, reverse('setup', args=[self.object.slug])),
            ('delete', ''),
        ]

    @property
    def cancel_url(self):
        return reverse('setup', args=[self.object.slug])

    def get_success_url(self):
        return reverse('setups')


class SetupListView(LoginRequiredMixin, generic.ListView):
    model = models.Setup
    title = 'Your Experiment Setups'

    def get_queryset(self):
        return super().get_queryset().filter(creator=self.request.user)
