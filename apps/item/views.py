import csv
from io import StringIO
from string import ascii_lowercase
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from apps.contrib import views as contrib_views
from apps.experiment import models as experiment_models

from . import forms
from . import models


class TextItemCreateView(LoginRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = models.TextItem
    title = 'Add Item'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.TextItemForm
    success_message = 'Item successfully created.'

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
            ('studies', reverse('studies')),
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('items', reverse('textitems', args=[study.slug, exp.slug])),
            ('create', '')
        ]


class TextItemUpdateView(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = models.TextItem
    title = 'Edit Item'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.TextItemForm
    success_message = 'Item successfully updated.'

    def get_success_url(self):
        exp = self.object.experiment
        return reverse('textitems', args=[exp.study.slug, exp.slug])

    @property
    def breadcrumbs(self):
        exp = self.object.experiment
        study = exp.study
        return [
            ('studies', reverse('studies')),
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('items', reverse('textitems', args=[study.slug, exp.slug])),
            (self.object, ''),
        ]


class TextItemDeleteView(LoginRequiredMixin, contrib_views.DefaultDeleteView):
    model = models.TextItem

    @property
    def breadcrumbs(self):
        exp = self.object.experiment
        study = exp.study
        return [
            ('studies', reverse('studies')),
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

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'validate':
            try:
                self.experiment.validate_items()
                messages.success(request, 'Items are valid.')
            except AssertionError as e:
                messages.error(request, str(e))
        return redirect('textitems',study_slug=self.experiment.study.slug, slug=self.experiment.slug)

    def get_queryset(self):
        return super().get_queryset().filter(experiment=self.experiment)

    @property
    def breadcrumbs(self):
        exp = self.experiment
        study = exp.study
        return [
            ('studies', reverse('studies')),
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('items', reverse('textitems', args=[study.slug, exp.slug])),
        ]


class ItemPregenerateView(LoginRequiredMixin, SuccessMessageMixin, generic.FormView):
    title = 'Pregenerate Items'
    form_class = forms.PregenerateItemsForm
    template_name = 'lrex_contrib/crispy_form.html'
    success_message = 'Items successfully generated.'

    def dispatch(self, *args, **kwargs):
        experiment_slug = self.kwargs['slug']
        self.experiment = experiment_models.Experiment.objects.get(slug=experiment_slug)
        return super().dispatch(*args, **kwargs)

    def _pregenerate_items(self, n_items, n_conditions):
        for n_item in range(1, n_items + 1):
            for condition in ascii_lowercase[:n_conditions]:
                models.TextItem.objects.create(
                    number=n_item,
                    condition=condition,
                    experiment=self.experiment,
                )

    def form_valid(self, form):
        result =  super().form_valid(form)
        n_items = form.cleaned_data['num_items']
        n_conditions = form.cleaned_data['num_conditions']
        self._pregenerate_items(n_items, n_conditions)
        return result

    def get_success_url(self):
        return reverse('textitems', args=[self.experiment.study.slug, self.experiment.slug])

    @property
    def breadcrumbs(self):
        exp = self.experiment
        study = exp.study
        return [
            ('studies', reverse('studies')),
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('items', reverse('textitems', args=[study.slug, exp.slug])),
            ('pregenerate', ''),
        ]


class TextItemUploadView(LoginRequiredMixin, SuccessMessageMixin, generic.FormView):
    title = 'Items'
    form_class = forms.UploadTextItemsForm
    template_name = 'lrex_contrib/crispy_form.html'
    success_message = 'Items loaded from file.'

    def dispatch(self, *args, **kwargs):
        experiment_slug = self.kwargs['slug']
        self.experiment = experiment_models.Experiment.objects.get(slug=experiment_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        result =  super().form_valid(form)
        file = form.cleaned_data['file']
        num_col = form.cleaned_data['number_column']
        cond_col = form.cleaned_data['condition_column']
        text_col = form.cleaned_data['text_column']
        data = file.read().decode()
        dialect = csv.Sniffer().sniff(data[:128])
        reader = csv.reader(StringIO(data), dialect)
        for row in reader:
            models.TextItem.objects.create(
                number=row[num_col - 1],
                condition=row[cond_col - 1],
                text=row[text_col - 1],
                experiment=self.experiment,
            )
        return result

    def get_success_url(self):
        return reverse('textitems', args=[self.experiment.study.slug, self.experiment.slug])

    @property
    def breadcrumbs(self):
        exp = self.experiment
        study = exp.study
        return [
            ('studies', reverse('studies')),
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('items', reverse('textitems', args=[study.slug, exp.slug])),
            ('upload', ''),
        ]


class ItemListListView(LoginRequiredMixin, generic.ListView):
    model = models.ItemList
    title = 'Item Lists'

    def dispatch(self, *args, **kwargs):
        experiment_slug = self.kwargs['slug']
        self.experiment = experiment_models.Experiment.objects.get(slug=experiment_slug)
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'generate_item_lists':
            self.experiment.compute_item_lists()
            messages.success(request, 'Item lists successfully generated.')
        return redirect('itemlists',study_slug=self.experiment.study.slug, slug=self.experiment.slug)


    def get_queryset(self):
        return models.ItemList.objects.filter(experiment=self.experiment)

    @property
    def breadcrumbs(self):
        exp = self.experiment
        study = exp.study
        return [
            ('studies', reverse('studies')),
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('itemlists', reverse('itemlists', args=[study.slug, exp.slug])),
        ]
