from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import generic

from apps.study import models as study_models

from . import forms
from . import models


class ExperimentDetailView(LoginRequiredMixin, generic.DetailView):
    model = models.Experiment
    title = 'Experiment Overview'

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.object.study.title, reverse('study', args=[self.object.study.slug])),
            ('experiments',reverse('experiments', args=[self.object.study.slug])),
            (self.object.title, '')
        ]


class ExperimentCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Experiment
    title = 'Create Experiment'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.ExperimentForm

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.study = self.study
        return super().form_valid(form)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            ('create','')
        ]


class ExperimentUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = models.Experiment
    title = 'Edit Experiment'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.ExperimentForm

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.object.study.title, reverse('study', args=[self.object.study.slug])),
            ('experiments',reverse('experiments', args=[self.object.study.slug])),
            (self.object.title, reverse('experiment', args=[self.object.study.slug, self.object.slug])),
            ('edit','')
        ]


class ExperimentDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = models.Experiment
    title = 'Delete Experiment'
    message = 'Delete Expriment?'

    @property
    def cancel_url(self):
        return reverse('experiments', args=[self.object.study.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.object.study.title, reverse('study', args=[self.object.study.slug])),
            ('experiments',reverse('experiments', args=[self.object.study.slug])),
            (self.object.title, reverse('experiment', args=[self.object.study.slug, self.object.slug])),
            ('delete','')
        ]

    def get_success_url(self):
        return reverse('experiments', args=[self.object.study.slug])


class ExperimentListView(LoginRequiredMixin, generic.ListView):
    model = models.Experiment
    title = 'Experiments'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(study=self.study)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study',args=[self.study.slug])),
            ('experiments','')
        ]


class ExperimentResultListView(LoginRequiredMixin, generic.ListView):
    model = models.Experiment
    title = 'Experiment Results'
    template_name = 'lrex_experiment/experiment_result_list.html'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(study=self.study)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study-run',args=[self.study.slug])),
            ('results','')
        ]


class ExperimentResultsView(LoginRequiredMixin, generic.DetailView):
    model = models.Experiment
    title = 'Experiment Results'
    template_name = 'lrex_experiment/experiment_results.html'

    @property
    def study(self):
        return self.object.study

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study-run',args=[self.study.slug])),
            ('results', reverse('experiment-result-list',args=[self.study.slug])),
            (self.object.title,'')
        ]
