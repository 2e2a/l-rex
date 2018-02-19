from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from apps.experiment import models as experiment_models

from . import models


class TextItemCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.TextItem
    fields = ['number', 'condition', 'text']
    title = 'Add Item'

    def dispatch(self, *args, **kwargs):
        experiment_slug = self.kwargs['slug']
        self.experiment = experiment_models.Experiment.objects.get(slug=experiment_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.experiment = self.experiment
        return super().form_valid(form)

    def get_success_url(self):
        exp = self.object.experiment
        return reverse('textitems', args=[exp.study.slug, exp.slug])

    @property
    def breadcrumbs(self):
        exp = self.experiment
        study = exp.study
        return [
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('items', reverse('textitems', args=[study.slug, exp.slug])),
            ('create', '')
        ]


class TextItemUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = models.TextItem
    fields = ['number', 'condition', 'text']
    title = 'Edit Item'

    def get_success_url(self):
        exp = self.object.experiment
        return reverse('textitems', args=[exp.study.slug, exp.slug])

    @property
    def breadcrumbs(self):
        exp = self.object.experiment
        study = exp.study
        return [
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('items', reverse('textitems', args=[study.slug, exp.slug])),
            (self.object, ''),
        ]


class TextItemDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = models.TextItem
    title = 'Delete Item'
    message = 'Delete Item?'

    @property
    def cancel_url(self):
        exp = self.object.experiment
        return reverse('textitems', args=[exp.study.slug, exp.slug])

    @property
    def breadcrumbs(self):
        exp = self.object.experiment
        study = exp.study
        return [
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('items', reverse('textitems', args=[study.slug, exp.slug])),
            (self.object, reverse('textitem-update', args=[study.slug, exp.slug, self.object.pk])),
            ('delete','')
        ]

    def get_success_url(self):
        exp = self.object.experiment
        return reverse('textitems', args=[exp.study.slug, exp.slug])


class TextItemListView(LoginRequiredMixin, generic.ListView):
    model = models.TextItem
    title = 'Items'

    def dispatch(self, *args, **kwargs):
        experiment_slug = self.kwargs['slug']
        self.experiment = experiment_models.Experiment.objects.get(slug=experiment_slug)
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(experiment=self.experiment)

    @property
    def breadcrumbs(self):
        exp = self.experiment
        study = exp.study
        return [
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('items', reverse('textitems', args=[study.slug, exp.slug])),
        ]


class ListListView(LoginRequiredMixin, generic.ListView):
    model = models.List
    title = 'Item Lists'

    def dispatch(self, *args, **kwargs):
        experiment_slug = self.kwargs['slug']
        self.experiment = experiment_models.Experiment.objects.get(slug=experiment_slug)
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'generate_lists':
            self.experiment.compute_lists()
        return redirect('itemlists',study_slug=self.experiment.study.slug, slug=self.experiment.slug)


    def get_queryset(self):
        return models.List.objects.filter(experiment=self.experiment)

    @property
    def breadcrumbs(self):
        exp = self.experiment
        study = exp.study
        return [
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('lists', reverse('itemlists', args=[study.slug, exp.slug])),
        ]
