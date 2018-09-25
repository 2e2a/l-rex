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
from apps.experiment import views as experiment_views
from apps.study import views as study_views

from . import forms
from . import models


class ItemMixin:
    item_object = None
    slug_url_kwarg = 'item_slug'

    @property
    def study(self):
        return self.experiment.study

    @property
    def experiment(self):
        return  self.item.experiment

    @property
    def item(self):
        if not self.item_object:
            item_slug = self.kwargs['item_slug']
            self.item_object = models.Item.objects.get(slug=item_slug)
        return self.item_object


class ItemObjectMixin(ItemMixin):

    @property
    def item(self):
        if not self.item_object:
            self.item_object =  self.get_object()
        return self.item_object


class ItemListView(LoginRequiredMixin, experiment_views.ExperimentMixin, study_views.NextStepsMixin, generic.ListView):
    model = models.Item
    title = 'Items'
    paginate_by = 16

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'validate':
            try:
                self.experiment.validate_items()
                self.experiment.set_progress(self.experiment.PROGRESS_EXP_ITEMS_VALIDATED)
                messages.success(self.request, study_views.progress_success_message(self.experiment.progress))
            except AssertionError as e:
                messages.error(request, str(e))
        return redirect('items', experiment_slug=self.experiment.slug)

    def get_queryset(self):
        return super().get_queryset().filter(experiment=self.experiment).order_by('number','condition')

    @property
    def consider_blocks(self):
        blocks = set()
        for item in self.object_list:
            blocks.add(item.block)
        return len(blocks) > 1

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.experiment.title, reverse('experiment', args=[self.experiment.slug])),
            ('items', ''),
        ]


class TextItemCreateView(LoginRequiredMixin, experiment_views.ExperimentMixin, generic.CreateView):
    model = models.TextItem
    title = 'Add item'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.TextItemForm

    def form_valid(self, form):
        form.instance.experiment = self.experiment
        result = super().form_valid(form)
        self.experiment.set_progress(experiment_models.Experiment.PROGRESS_EXP_ITEMS_CREATED)
        messages.success(self.request, study_views.progress_success_message(self.experiment.progress))
        return result

    def get_success_url(self):
        return reverse('items', args=[self.experiment.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.experiment.title, reverse('experiment', args=[self.experiment.slug])),
            ('items', reverse('items', args=[self.experiment.slug])),
            ('create', '')
        ]


class TextItemUpdateView(LoginRequiredMixin, SuccessMessageMixin, ItemObjectMixin, generic.UpdateView):
    model = models.TextItem
    title = 'Edit item'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.TextItemForm
    success_message = 'Item successfully updated.'

    def form_valid(self, form):
        result = super().form_valid(form)
        self.experiment.set_progress(self.experiment.PROGRESS_EXP_ITEMS_CREATED)
        return result

    def get_success_url(self):
        return reverse('items', args=[self.experiment.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.experiment.title, reverse('experiment', args=[self.experiment.slug])),
            ('items', reverse('items', args=[self.experiment.slug])),
            (self.item, ''),
        ]


class AudioLinkItemCreateView(LoginRequiredMixin, experiment_views.ExperimentMixin, generic.CreateView):
    model = models.AudioLinkItem
    title = 'Add Item'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.AudioLinkItemForm

    def form_valid(self, form):
        form.instance.experiment = self.experiment
        result = super().form_valid(form)
        self.experiment.set_progress(experiment_models.Experiment.PROGRESS_EXP_ITEMS_CREATED)
        messages.success(self.request, study_views.progress_success_message(self.experiment.progress))
        return result

    def get_success_url(self):
        return reverse('items', args=[self.experiment.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.experiment.title, reverse('experiment', args=[self.experiment.slug])),
            ('items', reverse('items', args=[self.experiment.slug])),
            ('create', '')
        ]


class AudioLinkItemUpdateView(LoginRequiredMixin, ItemObjectMixin, SuccessMessageMixin, generic.UpdateView):
    model = models.AudioLinkItem
    title = 'Edit Item'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.AudioLinkItemForm
    success_message = 'Item successfully updated.'

    def form_valid(self, form):
        result = super().form_valid(form)
        self.experiment.set_progress(self.experiment.PROGRESS_EXP_ITEMS_CREATED)
        return result

    def get_success_url(self):
        return reverse('items', args=[self.experiment.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.experiment.title, reverse('experiment', args=[self.experiment.slug])),
            ('items', reverse('items', args=[self.experiment.slug])),
            (self.item, ''),
        ]


class ItemDeleteView(LoginRequiredMixin, ItemObjectMixin, contrib_views.DefaultDeleteView):
    model = models.Item

    def delete(self, *args, **kwargs):
        response = super().delete(*args, **kwargs)
        if not models.Item.objects.filter(experiment=self.experiment).exists():
            self.experiment.set_progress(self.experiment.PROGRESS_EXP_CREATED)
        else:
            self.experiment.set_progress(self.experiment.PROGRESS_EXP_ITEMS_CREATED)
        return response

    def get_success_url(self):
        return reverse('items', args=[self.experiment.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.experiment.title, reverse('experiment', args=[self.experiment.slug])),
            ('items', reverse('items', args=[self.experiment.slug])),
            (self.item, reverse('text-item-update', args=[self.item.slug])),
            ('delete','')
        ]


class ItemPregenerateView(LoginRequiredMixin, experiment_views.ExperimentMixin, SuccessMessageMixin, generic.FormView):
    title = 'Pregenerate items'
    form_class = forms.PregenerateItemsForm
    template_name = 'lrex_contrib/crispy_form.html'
    success_message = 'Items successfully generated.'

    def _pregenerate_items(self, n_items, n_conditions):
        for n_item in range(1, n_items + 1):
            for condition in ascii_lowercase[:n_conditions]:
                if self.study.has_text_items:
                    models.TextItem.objects.create(
                        number=n_item,
                        condition=condition,
                        experiment=self.experiment,
                    )
                elif self.study.has_audiolink_items:
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
        return reverse('items', args=[self.experiment.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.experiment.title, reverse('experiment', args=[self.experiment.slug])),
            ('items', reverse('items', args=[self.experiment.slug])),
            ('pregenerate', ''),
        ]


class ItemUploadView(LoginRequiredMixin, experiment_views.ExperimentMixin, generic.FormView):
    title = 'Items'
    form_class = forms.UploadItemsForm
    template_name = 'lrex_contrib/crispy_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['questions'] = self.study.question_set.all()
        return kwargs

    def form_valid(self, form):
        result =  super().form_valid(form)
        models.Item.objects.filter(experiment=self.experiment).delete()

        file = form.cleaned_data['file']
        num_col = form.cleaned_data['number_column'] - 1
        cond_col = form.cleaned_data['condition_column'] - 1
        text_col = form.cleaned_data['text_column'] - 1
        block_col = form.cleaned_data['block_column'] - 1 if form.cleaned_data['block_column'] > 0 else None

        try:
            data = file.read().decode('utf-8')
        except UnicodeDecodeError:
            file.seek(0)
            data = file.read().decode('latin-1')
        data_len = len(data)
        sniff_data = data[:500 if data_len > 500 else data_len]
        has_header = csv.Sniffer().has_header(sniff_data)
        dialect = csv.Sniffer().sniff(sniff_data)
        reader = csv.reader(StringIO(data), dialect)

        if has_header:
            next(reader)

        for row in reader:
            item = None
            if self.study.has_text_items:
                item = models.TextItem.objects.create(
                    number=row[num_col],
                    condition=row[cond_col],
                    text=row[text_col],
                    experiment=self.experiment,
                    block=row[block_col] if block_col else 1,
                )
            elif self.study.has_audiolink_items:
                item = models.AudioLinkItem.objects.create(
                    number=row[num_col],
                    condition=row[cond_col],
                    url=row[text_col],
                    experiment=self.experiment,
                    block=row[block_col] if block_col else 1,
                )
            create_item_questions = False
            for i in range(self.study.question_set.count()):
                if form.cleaned_data['question_{}_question_column'.format(i+1)] > 0:
                    create_item_questions = True
                    break
            if create_item_questions:
                for i, question in enumerate(self.study.question_set.all()):
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
                    else:
                        models.ItemQuestion.objects.create(
                            item=item,
                            question=question,
                            scale_labels=None,
                            legend=None,
                        )


        self.experiment.set_progress(self.experiment.PROGRESS_EXP_ITEMS_CREATED)
        messages.success(self.request, study_views.progress_success_message(self.experiment.progress))
        return result

    def get_success_url(self):
        return reverse('items', args=[self.experiment.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.experiment.title, reverse('experiment', args=[self.experiment.slug])),
            ('items', reverse('items', args=[self.experiment.slug])),
            ('upload', ''),
        ]


class ItemDeleteAllView(LoginRequiredMixin, experiment_views.ExperimentMixin, generic.TemplateView):
    title = 'Confirm Delete'
    template_name = 'lrex_contrib/confirm_delete.html'
    message =  'Delete all items?'

    def post(self, request, *args, **kwargs):
        models.Item.objects.filter(experiment=self.experiment).delete()
        self.experiment.set_progress(self.experiment.PROGRESS_EXP_CREATED)
        messages.success(self.request, 'Deletion successfull.')
        return redirect(self.get_success_url())

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.experiment.title, reverse('experiment', args=[self.experiment.slug])),
            ('items', reverse('items', args=[self.experiment.slug])),
            ('delete-all','')
        ]

    def get_success_url(self):
        return reverse('items', args=[self.experiment.slug])


class ItemQuestionsUpdateView(LoginRequiredMixin, ItemMixin, study_views.NextStepsMixin, generic.TemplateView):
    title = 'Customize item questions'
    template_name = 'lrex_contrib/crispy_formset_form.html'
    formset = None
    helper = forms.itemquestion_formset_helper

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
                            self.formset.error_class(ValidationError('Invalid scale labels').error_list)
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
            (self.experiment.title, reverse('experiment', args=[self.experiment.slug])),
            ('items', reverse('items', args=[self.experiment.slug])),
            ('{}-questions'.format(self.item),'')
        ]


class ItemListListView(LoginRequiredMixin, experiment_views.ExperimentMixin, study_views.NextStepsMixin,
                       generic.ListView):
    model = models.ItemList
    title = 'Item lists'

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'generate_item_lists':
            self.experiment.compute_item_lists()
            self.experiment.set_progress(self.experiment.PROGRESS_EXP_LISTS_CREATED)
            messages.success(self.request, study_views.progress_success_message(self.experiment.progress))
        return redirect('itemlists', experiment_slug=self.experiment.slug)

    def get_queryset(self):
        return models.ItemList.objects.filter(experiment=self.experiment)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.experiment.title, reverse('experiment', args=[self.experiment.slug])),
            ('itemlists', ''),
        ]
