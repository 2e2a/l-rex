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
from apps.study import views as study_views

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

    @property
    def study(self):
        return self.experiment.study

    def form_valid(self, form):
        form.instance.experiment = self.experiment
        result = super().form_valid(form)
        self.study.progress = self.study.PROGRESS_EXP_ITEMS_CREATED
        self.study.save()
        if self.study.progress == self.study.PROGRESS_EXP_CREATED:
            messages.success(self.request, study_views.progress_success_message(self.study.progress))
        return result

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

    def form_valid(self, form):
        result = super().form_valid(form)
        self.study.progress = self.study.PROGRESS_EXP_ITEMS_CREATED
        self.study.save()
        return result

    @property
    def study(self):
        return self.object.experiment.study

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

    def delete(self, *args, **kwargs):
        response = super().delete(*args, **kwargs)
        experiment = self.object.experiment
        if not models.Item.objects.filter(experiment=experiment).exists():
            experiment.study.progress = experiment.study.PROGRESS_EXP_CREATED
        else:
            experiment.study.progress = experiment.study.PROGRESS_EXP_ITEMS_CREATED
        experiment.study.save()
        return response

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


class TextItemListView(LoginRequiredMixin, study_views.NextStepsMixin, generic.ListView):
    model = models.TextItem
    title = 'Items'

    @property
    def study(self):
        return self.experiment.study

    def dispatch(self, *args, **kwargs):
        experiment_slug = self.kwargs['slug']
        self.experiment = experiment_models.Experiment.objects.get(slug=experiment_slug)
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'validate':
            try:
                self.experiment.validate_items()
                self.study.progress = self.study.PROGRESS_EXP_ITEMS_VALIDATED
                messages.success(self.request, study_views.progress_success_message(self.study.progress))
                self.study.save()
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
        self.study.progress = self.study.PROGRESS_EXP_ITEMS_CREATED
        messages.success(self.request, study_views.progress_success_message(self.study.progress))
        self.study.save()
        return result

    def get_success_url(self):
        return reverse('textitems', args=[self.experiment.study.slug, self.experiment.slug])

    @property
    def study(self):
        return self.experiment.study

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


class TextItemUploadView(LoginRequiredMixin, generic.FormView):
    title = 'Items'
    form_class = forms.UploadTextItemsForm
    template_name = 'lrex_contrib/crispy_form.html'

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

        self.study.progress = self.study.PROGRESS_EXP_ITEMS_CREATED
        messages.success(self.request, study_views.progress_success_message(self.study.progress))
        self.study.save()
        return result

    def get_success_url(self):
        return reverse('textitems', args=[self.experiment.study.slug, self.experiment.slug])

    @property
    def study(self):
        return self.experiment.study

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



class TextItemDeleteAllView(LoginRequiredMixin, generic.TemplateView):
    title = 'Confirm Delete'
    template_name = 'lrex_contrib/confirm_delete.html'

    def post(self, request, *args, **kwargs):
        models.Item.objects.filter(experiment=self.experiment).delete()
        self.experiment.study.progress = self.experiment.study.PROGRESS_EXP_CREATED
        self.experiment.study.save()
        messages.success(self.request, 'Deletion successfull.')
        return redirect(self.get_success_url())

    def dispatch(self, *args, **kwargs):
        experiment_slug = self.kwargs['slug']
        self.experiment = experiment_models.Experiment.objects.get(slug=experiment_slug)
        return super().dispatch(*args, **kwargs)

    @property
    def breadcrumbs(self):
        study = self.experiment.study
        return [
            ('studies', reverse('studies')),
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (self.experiment.title, reverse('experiment', args=[study.slug, self.experiment.slug])),
            ('items', reverse('textitems', args=[study.slug, self.experiment.slug])),
            ('delete-all','')
        ]

    def get_success_url(self):
        return reverse('textitems', args=[self.experiment.study.slug, self.experiment.slug])


class ItemListListView(LoginRequiredMixin, study_views.NextStepsMixin, generic.ListView):
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
            self.study.progress = self.study.PROGRESS_EXP_LISTS_CREATED
            messages.success(self.request, study_views.progress_success_message(self.study.progress))
            self.study.save()
        return redirect('itemlists',study_slug=self.experiment.study.slug, slug=self.experiment.slug)

    def get_queryset(self):
        return models.ItemList.objects.filter(experiment=self.experiment)

    @property
    def study(self):
        return self.experiment.study

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
