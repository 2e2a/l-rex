import csv
from io import StringIO
from string import ascii_lowercase
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views import generic

from apps.contrib import views as contrib_views
from apps.contrib import csv as contrib_csv
from apps.experiment import views as experiment_views
from apps.study import models as study_models
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

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['study'] = self.study
        data['experiment'] = self.experiment
        data['item'] = self.item
        return data


class ItemObjectMixin(ItemMixin):

    @property
    def item(self):
        if not self.item_object:
            self.item_object =  self.get_object()
        return self.item_object


class ItemsValidateMixin:

    def validate_items(self):
        try:
            warnings = self.experiment.validate_items()
            messages.success(self.request, 'Items seem valid')
            for warning in warnings:
                messages.warning(self.request, 'Warning: {}'.format(warning))
        except AssertionError as e:
            messages.error(self.request, str(e))


class ItemListView(experiment_views.ExperimentMixin, study_views.CheckStudyCreatorMixin, study_views.NextStepsMixin,
                   study_views.DisableFormIfStudyActiveMixin, ItemsValidateMixin, generic.ListView):
    model = models.Item
    title = 'Items'
    paginate_by = 16

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'validate':
            self.validate_items()
        return redirect('items', experiment_slug=self.experiment.slug)

    def get_queryset(self):
        return super().get_queryset().filter(experiment=self.experiment).order_by('number','condition')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['consider_blocks'] = len(self.study.item_blocks) > 1
        return data

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.experiment.title, reverse('experiment', args=[self.experiment.slug])),
            ('items', ''),
        ]


class TextItemCreateView(experiment_views.ExperimentMixin, study_views.CheckStudyCreatorMixin,
                         study_views.DisableFormIfStudyActiveMixin, generic.CreateView):
    model = models.TextItem
    title = 'Add item'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.TextItemForm

    def form_valid(self, form):
        form.instance.experiment = self.experiment
        result = super().form_valid(form)
        messages.success(self.request, 'Item created')
        if self.experiment.is_complete:
            self.experiment.set_items_validated(False)
            self.experiment.delete_lists()
            msg = 'Note: Items have changed. Deleting old lists and questionnaires.'
            messages.info(self.request, msg)
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


class TextItemUpdateView(SuccessMessageMixin, ItemObjectMixin, study_views.CheckStudyCreatorMixin,
                         study_views.DisableFormIfStudyActiveMixin, generic.UpdateView):
    model = models.TextItem
    title = 'Edit item'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.TextItemForm
    success_message = 'Item successfully updated.'

    def form_valid(self, form):
        result =  super().form_valid(form)
        self.experiment.set_items_validated(False)
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


class AudioLinkItemCreateView(experiment_views.ExperimentMixin, study_views.CheckStudyCreatorMixin,
                              study_views.DisableFormIfStudyActiveMixin, generic.CreateView):
    model = models.AudioLinkItem
    title = 'Add Item'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.AudioLinkItemForm

    def form_valid(self, form):
        form.instance.experiment = self.experiment
        result = super().form_valid(form)
        messages.success(self.request, 'Item created')
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


class AudioLinkItemUpdateView(ItemObjectMixin, study_views.CheckStudyCreatorMixin, SuccessMessageMixin,
                              study_views.DisableFormIfStudyActiveMixin, generic.UpdateView):
    model = models.AudioLinkItem
    title = 'Edit Item'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.AudioLinkItemForm
    success_message = 'Item successfully updated.'

    def form_valid(self, form):
        result =  super().form_valid(form)
        self.experiment.set_items_validated(False)
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


class ItemDeleteView(ItemObjectMixin, study_views.CheckStudyCreatorMixin, study_views.DisableFormIfStudyActiveMixin,
                     contrib_views.DefaultDeleteView):
    model = models.Item

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        self.experiment.set_items_validated(False)
        self.experiment.delete_lists()
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
            (self.item, reverse('text-item-update', args=[self.item.slug])),
            ('delete','')
        ]


class ItemPregenerateView(experiment_views.ExperimentMixin, study_views.CheckStudyCreatorMixin, SuccessMessageMixin,
                          study_views.DisableFormIfStudyActiveMixin, generic.FormView):
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
        self.experiment.set_items_validated(False)
        self.experiment.delete_lists()
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


class ItemUploadView(experiment_views.ExperimentMixin, study_views.CheckStudyCreatorMixin, ItemsValidateMixin,
                     study_views.DisableFormIfStudyActiveMixin, generic.FormView):
    title = 'Items'
    form_class = forms.UploadItemsForm
    template_name = 'lrex_contrib/crispy_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.study.questions:
            msg = 'Note: If you want to use per item question customization, please define the study question first ' \
                  '(<a href="{}">here</a>)'.format(reverse('study-questions', args=[self.study.slug]))
            messages.info(self.request, mark_safe(msg))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['questions'] = self.study.questions
        return kwargs

    def form_valid(self, form):
        result = super().form_valid(form)

        new_items = []
        items_to_delete = list(models.Item.objects.filter(experiment=self.experiment).all())

        num_col = form.cleaned_data['number_column'] - 1
        cond_col = form.cleaned_data['condition_column'] - 1
        text_col = form.cleaned_data['text_column'] - 1
        block_col = form.cleaned_data['block_column'] - 1 if form.cleaned_data['block_column'] > 0 else None

        data = contrib_csv.read_file(form.cleaned_data)
        reader = csv.reader(
            StringIO(data), delimiter=form.detected_csv['delimiter'], quoting=form.detected_csv['quoting']
        )
        if form.detected_csv['has_header']:
            next(reader)
        for row in reader:
            if not row:
                continue
            item = None
            if self.study.has_text_items:
                item, created = models.TextItem.objects.get_or_create(
                    number=row[num_col],
                    condition=row[cond_col],
                    text=row[text_col],
                    experiment=self.experiment,
                    block=row[block_col] if block_col else 1,
                )
            elif self.study.has_audiolink_items:
                item, created = models.AudioLinkItem.objects.get_or_create(
                    number=row[num_col],
                    condition=row[cond_col],
                    url=row[text_col],
                    experiment=self.experiment,
                    block=row[block_col] if block_col else 1,
                )

            if created:
                new_items.append(item)
            else:
                items_to_delete.remove(item)

            create_item_questions = False
            for question in self.study.questions:
                if form.cleaned_data['question_{}_question_column'.format(question.number)] > 0:
                    create_item_questions = True
                    break
            if create_item_questions:
                for question in self.study.questions:
                    question_col = form.cleaned_data['question_{}_question_column'.format(question.number)] - 1
                    if question_col > 0:
                        scale_col = form.cleaned_data['question_{}_scale_column'.format(question.number)] - 1
                        legend_col = form.cleaned_data['question_{}_legend_column'.format(question.number)] - 1
                        models.ItemQuestion.objects.get_or_create(
                            item=item,
                            question=row[question_col],
                            scale_labels=row[scale_col] if scale_col>0 else None,
                            legend=row[legend_col] if legend_col>0 else None,
                        )
        messages.success(self.request, 'Items uploaded')
        if new_items or items_to_delete and self.experiment.is_complete:
            self.experiment.delete_lists()
            msg = 'Note: Items have changed. Deleting old lists and questionnaires.'
            messages.info(self.request, msg)
        for item in items_to_delete:
            item.delete()
        self.validate_items()
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


class ItemDeleteAllView(experiment_views.ExperimentMixin, study_views.CheckStudyCreatorMixin,
                        study_views.DisableFormIfStudyActiveMixin, generic.TemplateView):
    title = 'Confirm Delete'
    template_name = 'lrex_contrib/confirm_delete.html'
    message =  'Delete all items?'

    def post(self, request, *args, **kwargs):
        models.Item.objects.filter(experiment=self.experiment).delete()
        self.experiment.set_items_validated(False)
        self.experiment.delete_lists()
        messages.success(self.request, 'All items deleted')
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


class ItemQuestionsUpdateView(ItemMixin, study_views.CheckStudyCreatorMixin, study_views.NextStepsMixin,
                              study_views.DisableFormIfStudyActiveMixin, generic.TemplateView):
    title = 'Customize item questions'
    template_name = 'lrex_contrib/crispy_formset_form.html'
    formset = None
    helper = forms.itemquestion_formset_helper

    def get(self, request, *args, **kwargs):
        n_questions = len(self.study.questions)
        item_questions_q =models.ItemQuestion.objects.filter(item=self.item)
        self.formset = forms.itemquestion_factory(n_questions, n_item_questions=item_questions_q.count())(
            queryset=item_questions_q
        )
        forms.initialize_with_questions(self.formset, self.study.questions)
        if n_questions == 0:
            msg = 'Note: If you want to use per item question customization, please define the study question first ' \
                  '(<a href="{}">here</a>)'.format(reverse('study-questions', args=[self.study.slug]))
            messages.info(self.request, mark_safe(msg))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        n_questions = len(self.study.questions)
        if 'submit' in request.POST:
            self.formset = forms.itemquestion_factory(n_questions)(request.POST, request.FILES)
            if self.formset.is_valid():
                instances = self.formset.save(commit=False)
                scale_labels_valid = True
                for instance, question in zip(instances, self.study.questions):
                    if instance.scale_labels \
                            and len(instance.scale_labels.split(',')) != question.scalevalue_set.count():
                        self.formset._errors[question.number]['scale_labels'] = \
                            self.formset.error_class(ValidationError('Invalid scale labels').error_list)
                        scale_labels_valid = False
                        break
                    instance.number = question.number
                    instance.item = self.item

                if scale_labels_valid:
                    for instance in instances:
                        instance.save()
                    return redirect('items', experiment_slug=self.experiment.slug)
        else: # reset
            self.item.itemquestion_set.all().delete()
            return self.get(request, *args, **kwargs)
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


class ItemListListView(experiment_views.ExperimentMixin, study_views.CheckStudyCreatorMixin, study_views.NextStepsMixin,
                       study_views.DisableFormIfStudyActiveMixin, generic.ListView):
    model = models.ItemList
    title = 'Item lists'

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'generate_distributed':
            self.experiment.compute_item_lists(distribute=True)
        elif action and action == 'generate_single':
            self.experiment.compute_item_lists(distribute=False)
        messages.success(self.request, 'Item lists generated.')
        if self.study.has_questionnaires:
            self.study.delete_questionnaires()
            messages.info(self.request, 'Old questionnaires deleted.')
        return redirect('itemlists', experiment_slug=self.experiment.slug)

    def get_queryset(self):
        return models.ItemList.objects.filter(experiment=self.experiment)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['allow_actions'] = self.experiment.items_validated
        return data

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.experiment.title, reverse('experiment', args=[self.experiment.slug])),
            ('itemlists', ''),
        ]


class ItemListUploadView(experiment_views.ExperimentMixin, study_views.CheckStudyCreatorMixin,
                         study_views.DisableFormIfStudyActiveMixin, generic.FormView):
    title = 'Upload custom item lists'
    form_class = forms.UploadItemListForm
    template_name = 'lrex_contrib/crispy_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['experiment'] = self.experiment
        return kwargs

    def form_valid(self, form):
        result =  super().form_valid(form)
        self.experiment.itemlist_set.all().delete()
        file = form.cleaned_data['file']
        list_col = form.cleaned_data['list_column'] - 1
        num_col = form.cleaned_data['item_number_column'] - 1
        cond_col = form.cleaned_data['item_condition_column'] - 1
        try:
            data = file.read().decode('utf-8')
        except UnicodeDecodeError:
            file.seek(0)
            data = file.read().decode('latin-1')
        data_len = len(data)
        sniff_data = data[:16 if data_len > 16 else data_len]
        has_header = csv.Sniffer().has_header(sniff_data)
        dialect = csv.Sniffer().sniff(sniff_data)
        reader = csv.reader(StringIO(data), dialect)
        if has_header:
            next(reader)
        items = []
        list_num_last = None
        for row in reader:
            if not row:
                continue
            list_num = row[list_col]
            if list_num_last and list_num_last != list_num:
                itemlist = models.ItemList.objects.create(experiment=self.experiment)
                itemlist.items.set(items)
                items = []
            item = self.experiment.item_set.get(number=row[num_col], condition=row[cond_col])
            items.append(item)
            list_num_last = list_num
        itemlist = models.ItemList.objects.create(experiment=self.experiment)
        itemlist.items.set(items)
        messages.success(self.request, 'Lists uploaded.')
        return result

    def get_success_url(self):
        return reverse('itemlists', args=[self.experiment.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.experiment.title, reverse('experiment', args=[self.experiment.slug])),
            ('itemlists', reverse('itemlists', args=[self.experiment.slug])),
            ('upload', ''),
        ]


