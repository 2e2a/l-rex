from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import generic

from apps.setup import models as setup_models

from . import models


class ExperimentDetailView(LoginRequiredMixin, generic.DetailView):
    model = models.Experiment
    title = 'Experiment Overview'

    @property
    def breadcrumbs(self):
        return [
            ('setups', reverse('setups')),
            (self.object.setup.title, reverse('setup', args=[self.object.setup.slug])),
            ('experiments',reverse('experiments', args=[self.object.setup.slug])),
            (self.object.title, '')
        ]


class ExperimentCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Experiment
    fields = ['title']
    title = 'Create Experiment'

    def dispatch(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        self.setup = setup_models.Setup.objects.get(slug=setup_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.setup = self.setup
        return super().form_valid(form)

    @property
    def breadcrumbs(self):
        return [
            ('setups', reverse('setups')),
            (self.setup.title, reverse('setup', args=[self.setup.slug])),
            ('experiments',reverse('experiments', args=[self.setup.slug])),
            ('create','')
        ]


class ExperimentUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = models.Experiment
    fields = ['title']
    title = 'Edit Experiment'

    @property
    def breadcrumbs(self):
        return [
            ('setups', reverse('setups')),
            (self.object.setup.title, reverse('setup', args=[self.object.setup.slug])),
            ('experiments',reverse('experiments', args=[self.object.setup.slug])),
            (self.object.title, reverse('experiment', args=[self.object.setup.slug, self.object.slug])),
            ('edit','')
        ]


class ExperimentDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = models.Experiment
    title = 'Delete Experiment'
    message = 'Delete Expriment?'

    @property
    def cancel_url(self):
        return reverse('experiment', args=[self.setup.slug, self.object.slug])

    @property
    def breadcrumbs(self):
        return [
            ('setups', reverse('setups')),
            (self.object.setup.title, reverse('setup', args=[self.object.setup.slug])),
            ('experiments',reverse('experiments', args=[self.object.setup.slug])),
            (self.object.title, reverse('experiment', args=[self.object.setup.slug, self.object.slug])),
            ('delete','')
        ]

    def get_success_url(self):
        return reverse('experiments', args=[self.object.setup.slug])


class ExperimentListView(LoginRequiredMixin, generic.ListView):
    model = models.Experiment
    title = 'Experiments'

    def dispatch(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        self.setup = setup_models.Setup.objects.get(slug=setup_slug)
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(setup=self.setup)

    @property
    def breadcrumbs(self):
        return [
            ('setups', reverse('setups')),
            (self.setup.title, reverse('setup',args=[self.setup.slug])),
            ('experiments','')
        ]