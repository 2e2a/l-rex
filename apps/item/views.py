import csv
from io import StringIO
from string import ascii_lowercase
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from apps.contrib import views as contrib_views
from apps.experiment import models as experiment_models
from apps.study import views as study_views

from . import forms
from . import models


class TextItemCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.TextItem
    title = 'Add item'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.TextItemForm

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
        self.experiment.set_progress(experiment_models.Experiment.PROGRESS_EXP_ITEMS_CREATED)
        messages.success(self.request, study_views.progress_success_message(self.experiment.progress))
        return result

    def get_success_url(self):
        exp = self.object.experiment
        return reverse('items', args=[exp.study.slug, exp.slug])

    @property
    def breadcrumbs(self):
        exp = self.experiment
        study = exp.study
        return [
            ('studies', reverse('studies')),
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('items', reverse('items', args=[study.slug, exp.slug])),
            ('create', '')
        ]


class TextItemUpdateView(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = models.TextItem
    title = 'Edit item'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.TextItemForm
    success_message = 'Item successfully updated.'

    def form_valid(self, form):
        result = super().form_valid(form)
        self.object.experiment.set_progress(self.object.experiment.PROGRESS_EXP_ITEMS_CREATED)
        return result

    @property
    def study(self):
        return self.object.experiment.study

    def get_success_url(self):
        exp = self.object.experiment
        return reverse('items', args=[exp.study.slug, exp.slug])

    @property
    def breadcrumbs(self):
        exp = self.object.experiment
        study = exp.study
        return [
            ('studies', reverse('studies')),
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('items', reverse('items', args=[study.slug, exp.slug])),
            (self.object, ''),
        ]


class AudioLinkItemCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.AudioLinkItem
    title = 'Add Item'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.AudioLinkItemForm

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
        self.experiment.set_progress(experiment_models.Experiment.PROGRESS_EXP_ITEMS_CREATED)
        messages.success(self.request, study_views.progress_success_message(self.experiment.progress))
        return result

    def get_success_url(self):
        exp = self.object.experiment
        return reverse('items', args=[exp.study.slug, exp.slug])

    @property
    def breadcrumbs(self):
        exp = self.experiment
        study = exp.study
        return [
            ('studies', reverse('studies')),
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('items', reverse('items', args=[study.slug, exp.slug])),
            ('create', '')
        ]


class AudioLinkItemUpdateView(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = models.AudioLinkItem
    title = 'Edit Item'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.AudioLinkItemForm
    success_message = 'Item successfully updated.'

    def form_valid(self, form):
        result = super().form_valid(form)
        self.object.experiment.set_progress(self.object.experiment.PROGRESS_EXP_ITEMS_CREATED)
        return result

    @property
    def study(self):
        return self.object.experiment.study

    def get_success_url(self):
        exp = self.object.experiment
        return reverse('items', args=[exp.study.slug, exp.slug])

    @property
    def breadcrumbs(self):
        exp = self.object.experiment
        study = exp.study
        return [
            ('studies', reverse('studies')),
            (study.title, reverse('study', args=[study.slug])),
            ('experiments',reverse('experiments', args=[study.slug])),
            (exp.title, reverse('experiment', args=[study.slug, exp.slug])),
            ('items', reverse('items', args=[study.slug, exp.slug])),
            (self.object, ''),
        ]


class ItemDeleteView(LoginRequiredMixin, contrib_views.DefaultDeleteView):
    model = models.Item

    def delete(self, *args, **kwargs):
        response = super().delete(*args, **kwargs)
        experiment = self.object.experiment
        if not models.Item.objects.filter(experiment=experiment).exists():
            experiment.set_progress(experiment.PROGRESS_EXP_CREATED)
        else:
            experiment.set_progress(experiment.PROGRESS_EXP_ITEMS_CREATED)
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
            ('items', reverse('items', args=[study.slug, exp.slug])),
            (self.object, reverse('text-item-update', args=[study.slug, exp.slug, self.object.pk])),
            ('delete','')
        ]

    def get_success_url(self):
        exp = self.object.experiment
        return reverse('items', args=[exp.study.slug, exp.slug])


class ItemListView(LoginRequiredMixin, study_views.NextStepsMixin, generic.ListView):
    model = models.Item
    title = 'Items'
    paginate_by = 16

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
                self.experiment.set_progress(self.experiment.PROGRESS_EXP_ITEMS_VALIDATED)
                messages.success(self.request, study_views.progress_success_message(self.experiment.progress))
            except AssertionError as e:
                messages.error(request, str(e))
        return redirect('items',study_slug=self.experiment.study.slug, slug=self.experiment.slug)

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
            ('items', reverse('items', args=[study.slug, exp.slug])),
        ]


class ItemPregenerateView(LoginRequiredMixin, SuccessMessageMixin, generic.FormView):
    title = 'Pregenerate items'
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
                if self.experiment.study.has_text_items:
                    models.TextItem.objects.create(
                        number=n_item,
                        condition=condition,
                        experiment=self.experiment,
                    )
                elif self.experiment.study.has_audiolink_items:
                    models.AudioLinkItem.objects.create(
                        number=n_item,
                        condition=condition,
                        experiment=self.experiment,
                    )


    def form_valid(self, form):
        result =  super().form_valid(form)
        n_items = form.cleaned_data['num_items']
        n_conditions = form.cleaned_data['num_conditions']
        models.Item.objects.filter(experiment=self.experiment).delete()
        self._pregenerate_items(n_items, n_conditions)
        return result

    def get_success_url(self):
        return reverse('items', args=[self.experiment.study.slug, self.experiment.slug])

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
            ('items', reverse('items', args=[study.slug, exp.slug])),
            ('pregenerate', ''),
        ]


class ItemUploadView(LoginRequiredMixin, generic.FormView):
    title = 'Items'
    form_class = forms.UploadItemsForm
    template_name = 'lrex_contrib/crispy_form.html'

    def dispatch(self, *args, **kwargs):
        experiment_slug = self.kwargs['slug']
        self.experiment = experiment_models.Experiment.objects.get(slug=experiment_slug)
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['questions'] = self.experiment.study.question_set.all()
        return kwargs

    def form_valid(self, form):
        result =  super().form_valid(form)
        models.Item.objects.filter(experiment=self.experiment).delete()

        file = form.cleaned_data['file']
        num_col = form.cleaned_data['number_column'] - 1
        cond_col = form.cleaned_data['condition_column'] - 1
        text_col = form.cleaned_data['text_column'] - 1

        try:
            data = file.read().decode('utf-8')
        except UnicodeDecodeError:
            file.seek(0)
            data = file.read().decode('latin-1')
        has_header = csv.Sniffer().has_header(data[:128])
        dialect = csv.Sniffer().sniff(data[:128])
        reader = csv.reader(StringIO(data), dialect)

        if has_header:
            next(reader)

        for row in reader:
            item = None
            if self.experiment.study.has_text_items:
                item = models.TextItem.objects.create(
                    number=row[num_col],
                    condition=row[cond_col],
                    text=row[text_col],
                    experiment=self.experiment,
                )
            elif self.experiment.study.has_audiolink_items:
                item = models.AudioLinkItem.objects.create(
                    number=row[num_col],
                    condition=row[cond_col],
                    url=row[text_col],
                    experiment=self.experiment,
                )
            for i, question in enumerate(self.experiment.study.question_set.all()):
                question_col = form.cleaned_data['question_{}_question_column'.format(i+1)] - 1
                if question_col > 0:
                    scale_col = form.cleaned_data['question_{}_scale_column'.format(i+1)] - 1
                    legend_col = form.cleaned_data['question_{}_legend_column'.format(i+1)] - 1
                    models.ItemQuestion.objects.create(
                        item=item,
                        question=row[question_col],
                        scale_labels=row[scale_col] if scale_col>0 else None,
                        legend=row[legend_col] if legend_col>0 else None,
                    )

        self.experiment.set_progress(self.experiment.PROGRESS_EXP_ITEMS_CREATED)
        messages.success(self.request, study_views.progress_success_message(self.experiment.progress))
        return result

    def get_success_url(self):
        return reverse('items', args=[self.experiment.study.slug, self.experiment.slug])

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
            ('items', reverse('items', args=[study.slug, exp.slug])),
            ('upload', ''),
        ]


class ItemDeleteAllView(LoginRequiredMixin, generic.TemplateView):
    title = 'Confirm Delete'
    template_name = 'lrex_contrib/confirm_delete.html'
    message =  'Delete all items?'

    def post(self, request, *args, **kwargs):
        models.Item.objects.filter(experiment=self.experiment).delete()
        self.experiment.set_progress(self.experiment.PROGRESS_EXP_CREATED)
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
            ('items', reverse('items', args=[study.slug, self.experiment.slug])),
            ('delete-all','')
        ]

    def get_success_url(self):
        return reverse('items', args=[self.experiment.study.slug, self.experiment.slug])


class ItemListListView(LoginRequiredMixin, study_views.NextStepsMixin, generic.ListView):
    model = models.ItemList
    title = 'Item lists'

    def dispatch(self, *args, **kwargs):
        experiment_slug = self.kwargs['slug']
        self.experiment = experiment_models.Experiment.objects.get(slug=experiment_slug)
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'generate_item_lists':
            self.experiment.compute_item_lists()
            self.experiment.set_progress(self.experiment.PROGRESS_EXP_LISTS_CREATED)
            messages.success(self.request, study_views.progress_success_message(self.experiment.progress))
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


class ItemQuestionsUpdateView(LoginRequiredMixin, study_views.NextStepsMixin, generic.TemplateView):
    title = 'Customize item questions'
    template_name = 'lrex_contrib/crispy_formset_form.html'

    formset = None
    helper = forms.itemquestion_formset_helper

    @property
    def study(self):
        return self.experiment.study

    def dispatch(self, *args, **kwargs):
        experiment_slug = kwargs.get('slug')
        self.experiment = experiment_models.Experiment.objects.get(slug=experiment_slug)
        item_pk = self.kwargs.get('pk')
        self.item = models.Item.objects.get(pk=item_pk)
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.formset = forms.itemquestion_factory(self.study.question_set.count())(
            queryset=models.ItemQuestion.objects.filter(item=self.item)
        )
        forms.initialize_with_questions(self.formset, self.study.question_set.all())
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        n_questions = self.study.question_set.count()
        if 'submit' in request.POST:
            self.formset = forms.itemquestion_factory(n_questions)(request.POST, request.FILES)
            if self.formset.is_valid():
                instances = self.formset.save(commit=False)
                scale_labels_valid = True
                for i, (instance, question) in enumerate(zip(instances, self.study.question_set.all())):
                    if instance.scale_labels \
                            and len(instance.scale_labels.split(',')) != question.scalevalue_set.count():
                        self.formset._errors[i]['scale_labels'] = \
                            self.formset.error_class(ValidationError('TEST').error_list)
                        scale_labels_valid = False
                        break
                    instance.item = self.item

                if scale_labels_valid:
                    for instance in instances:
                        instance.save()
        else: # reset
            self.item.itemquestion_set.all().delete()
        forms.initialize_with_questions(self.formset, self.study.question_set.all())
        return super().get(request, *args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.experiment.title, reverse('experiment', args=[self.study.slug, self.experiment.slug])),
            ('items', reverse('items', args=[self.study.slug, self.experiment.slug])),
            ('{}-questions'.format(self.item),'')
        ]
