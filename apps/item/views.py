from io import StringIO
from string import ascii_lowercase
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views import generic

from apps.contrib import views as contrib_views
from apps.contrib import csv as contrib_csv
from apps.materials import views as materials_views
from apps.study import views as study_views

from . import forms
from . import models


class ItemMixin:
    item_object = None
    slug_url_kwarg = 'item_slug'

    @property
    def study(self):
        return self.materials.study

    @property
    def materials(self):
        return  self.item.materials

    @property
    def item(self):
        if not self.item_object:
            item_slug = self.kwargs['item_slug']
            self.item_object = models.Item.objects.get(slug=item_slug)
        return self.item_object

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['study'] = self.study
        data['materials'] = self.materials
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
            warnings = self.materials.validate_items()
            messages.success(self.request, 'Items seem valid.')
            for warning in warnings:
                messages.warning(self.request, '{}'.format(warning))
            lists_url = reverse('itemlists', args=[self.materials.slug])
            msg = 'Lists automatically generated. <a href="{}">Check lists.</a>'.format(lists_url)
            messages.success(self.request, mark_safe(msg))
            if self.study.has_questionnaires:
                self.study.delete_questionnaires()
                messages.info(self.request, 'Old questionnaires deleted.')
        except AssertionError as e:
            messages.error(self.request, str(e))


class ItemListView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    contrib_views.ActionsMixin,
    materials_views.MaterialsNavMixin,
    ItemsValidateMixin,
    generic.ListView
):
    model = models.Item
    paginate_by = 16

    @property
    def title(self):
        return '{}: Items'.format(self.materials.title)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'validate':
            self.validate_items()
        return redirect('items', materials_slug=self.materials.slug)

    def get_queryset(self):
        return super().get_queryset().filter(materials=self.materials).order_by('number','condition')

    def _add_page(self, url, page=None):
        if not page:
            page = self.request.GET.get(self.page_kwarg, None)
        if page:
            url += '?page={}'.format(page)
        return url

    @property
    def _item_add_url(self):
        if self.study.has_text_items:
            url_name = 'text-item-create'
        elif self.study.has_markdown_items:
            url_name = 'markdown-item-create'
        else:
            url_name = 'audio-link-item-create'
        url = reverse(url_name, args=[self.materials.slug])
        return url

    @property
    def _item_edit_url_name(self):
        if self.study.has_text_items:
            return 'text-item-update'
        elif self.study.has_markdown_items:
            return 'markdown-item-update'
        else:
            return 'audio-link-item-update'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['item_edit_url_name'] = self._item_edit_url_name
        return data

    @property
    def actions(self):
        return [
            ('link', 'Upload CSV', reverse('items-upload', args=[self.materials.slug]), self.ACTION_CSS_BUTTON_SECONDARY),
            ('button', 'Validate / generate lists', 'validate', self.ACTION_CSS_BUTTON_PRIMARY),
        ]

    @property
    def secondary_actions(self):
        actions = [
            ('link', 'Add item', self._add_page(self._item_add_url)),
            ('link', 'Pregenerate items', reverse('items-pregenerate', args=[self.materials.slug])),
            ('link', 'Download CSV', reverse('items-download', args=[self.materials.slug])),
            ('link', 'Delete all items', reverse('items-delete', args=[self.materials.slug])),
            ('link', 'Delete materials', reverse('materials-delete', args=[self.materials.slug])),
        ]
        if self.study.enable_item_rating_feedback:
            actions.insert(
                2,
                ('Upload Feedback', self._add_page(reverse('items-upload-feedback', args=[self.materials.slug])))
            )
        return actions

    @property
    def disable_actions(self):
        if self.is_disabled:
            return [1, 2], [0, 1]

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.materials.slug])),
            ('items', ''),
        ]


class ItemCreateMixin(contrib_views.PaginationHelperMixin, materials_views.MaterialsNavMixin):
    title = 'Add item'
    template_name = 'lrex_contrib/crispy_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'add_save': True,
            'materials': self.materials,
        })
        return kwargs

    def form_valid(self, form):
        form.instance.materials = self.materials
        result = super().form_valid(form)
        messages.success(self.request, 'Item created')
        if self.materials.is_complete:
            self.materials.set_items_validated(False)
            self.materials.delete_lists()
            msg = 'Note: Items have changed. Deleting old lists and questionnaires.'
            messages.info(self.request, msg)
        return result

    def get_success_url(self):
        if 'save' in self.request.POST:
            return self.url_paginated(self.object.get_absolute_url())
        item_pos = self.materials.item_pos(self.object)
        item_page = int(item_pos / ItemListView.paginate_by) + 1
        return self.reverse_paginated('items', args=[self.materials.slug], page=item_page)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.materials.slug])),
            ('items', self.reverse_paginated('items', args=[self.materials.slug])),
            ('create', '')
        ]


class ItemUpdateMixin(
    contrib_views.LeaveWarningMixin,
    contrib_views.PaginationHelperMixin,
    materials_views.MaterialsNavMixin,
):
    title = 'Edit item'
    template_name = 'lrex_contrib/crispy_form.html'
    success_message = 'Item successfully updated.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'add_save': True,
            'materials': self.materials,
        })
        return kwargs

    def form_valid(self, form):
        result =  super().form_valid(form)
        self.materials.set_items_validated(False)
        return result

    def get_success_url(self):
        if 'save' in self.request.POST:
            return self.url_paginated(self.object.get_absolute_url())
        return self.reverse_paginated('items', args=[self.materials.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.materials.slug])),
            ('items', self.reverse_paginated('items', args=[self.materials.slug])),
            (self.item, ''),
        ]


class TextItemCreateView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    ItemCreateMixin,
    generic.CreateView
):
    model = models.TextItem
    form_class = forms.TextItemForm


class TextItemUpdateView(
    SuccessMessageMixin,
    ItemObjectMixin,
    study_views.CheckStudyCreatorMixin,
    ItemUpdateMixin,
    study_views.DisableFormIfStudyActiveMixin,
    generic.UpdateView
):
    model = models.TextItem
    form_class = forms.TextItemForm


class MarkdownItemCreateView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    ItemCreateMixin,
    generic.CreateView
):
    model = models.MarkdownItem
    form_class = forms.MarkdownItemForm


class MarkdownItemUpdateView(
    SuccessMessageMixin,
    ItemObjectMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    ItemUpdateMixin,
    generic.UpdateView
):
    model = models.MarkdownItem
    form_class = forms.MarkdownItemForm


class AudioLinkItemCreateView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    ItemCreateMixin,
    generic.CreateView
):
    model = models.AudioLinkItem
    form_class = forms.AudioLinkItemForm


class AudioLinkItemUpdateView(
    ItemObjectMixin,
    study_views.CheckStudyCreatorMixin,
    SuccessMessageMixin,
    study_views.DisableFormIfStudyActiveMixin,
    ItemUpdateMixin,
    generic.UpdateView
):
    model = models.AudioLinkItem
    form_class = forms.AudioLinkItemForm


class ItemDeleteView(
    ItemObjectMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    contrib_views.PaginationHelperMixin,
    materials_views.MaterialsNavMixin,
    contrib_views.DefaultDeleteView
):
    model = models.Item

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        self.materials.set_items_validated(False)
        self.materials.delete_lists()
        return result

    def get_success_url(self):
        return self.reverse_paginated('items', args=[self.materials.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.materials.slug])),
            ('items', self.reverse_paginated('items', args=[self.materials.slug])),
            (self.item, self.reverse_paginated('text-item-update', args=[self.item.slug])),
            ('delete','')
        ]


class ItemPregenerateView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    SuccessMessageMixin,
    study_views.DisableFormIfStudyActiveMixin,
    contrib_views.PaginationHelperMixin,
    materials_views.MaterialsNavMixin,
    generic.FormView
):
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
                        materials=self.materials,
                    )
                elif self.study.has_markdown_items:
                    models.TextItem.objects.create(
                        number=n_item,
                        condition=condition,
                        materials=self.materials,
                    )
                elif self.study.has_audiolink_items:
                    models.AudioLinkItem.objects.create(
                        number=n_item,
                        condition=condition,
                        materials=self.materials,
                    )

    def form_valid(self, form):
        result =  super().form_valid(form)
        n_items = form.cleaned_data['num_items']
        n_conditions = form.cleaned_data['num_conditions']
        models.Item.objects.filter(materials=self.materials).delete()
        self.materials.set_items_validated(False)
        self.materials.delete_lists()
        self._pregenerate_items(n_items, n_conditions)
        return result

    def get_success_url(self):
        return self.reverse_paginated('items', args=[self.materials.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.materials.slug])),
            ('items', self.reverse_paginated('items', args=[self.materials.slug])),
            ('pregenerate', ''),
        ]


class ItemUploadView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    ItemsValidateMixin,
    study_views.DisableFormIfStudyActiveMixin,
    generic.FormView
):
    title = 'Items'
    form_class = forms.ItemUploadForm
    template_name = 'lrex_contrib/crispy_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.study.questions:
            msg = 'Note: If you want to use per item question customization, please ' \
                  '<a href="{}">define the study question</a> first.'.format(
                    reverse('study-questions', args=[self.study.slug]))
            messages.info(self.request, mark_safe(msg))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['materials'] = self.materials
        return kwargs

    def form_valid(self, form):
        result = super().form_valid(form)
        columns = {
            'item': form.cleaned_data['number_column'] - 1,
            'condition': form.cleaned_data['condition_column'] - 1,
            'content': form.cleaned_data['content_column'] - 1,
        }
        if form.cleaned_data['block_column'] > 0:
            columns.update({'block': form.cleaned_data['block_column'] - 1})
        if self.study.has_audiolink_items:
            columns.update({'audio_description': form.cleaned_data['audio_description_column'] - 1})
        for i, question in enumerate(self.study.questions):
            question_column = 'question_{}_question_column'.format(question.number + 1)
            if form.cleaned_data[question_column] > 0:
                columns.update({'question{}'.format(i): form.cleaned_data[question_column] - 1})
            scale_column = 'question_{}_scale_column'.format(question.number + 1)
            if form.cleaned_data[scale_column] > 0:
                columns.update({'scale{}'.format(i): form.cleaned_data[scale_column] - 1})
            legend_column = 'question_{}_legend_column'.format(question.number + 1)
            if form.cleaned_data[legend_column] > 0:
                columns.update({'legend{}'.format(i): form.cleaned_data[legend_column] - 1})
        data = StringIO(contrib_csv.read_file(form.cleaned_data))
        self.materials.items_csv_create(data, has_materials_column=False, user_columns=columns, detected_csv=form.detected_csv)
        messages.success(self.request, 'Items uploaded.')
        self.validate_items()
        return result

    def get_success_url(self):
        return reverse('items', args=[self.materials.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.materials.slug])),
            ('items', reverse('items', args=[self.materials.slug])),
            ('upload', ''),
        ]


class ItemDeleteAllView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    generic.TemplateView
):
    title = 'Confirm Delete'
    template_name = 'lrex_contrib/confirm_delete.html'
    message =  'Delete all items?'

    def post(self, request, *args, **kwargs):
        models.Item.objects.filter(materials=self.materials).delete()
        self.materials.set_items_validated(False)
        self.materials.delete_lists()
        messages.success(self.request, 'All items deleted.')
        return redirect(self.get_success_url())

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.materials.slug])),
            ('items', reverse('items', args=[self.materials.slug])),
            ('delete-all','')
        ]

    def get_success_url(self):
        return reverse('items', args=[self.materials.slug])


class ItemQuestionsUpdateView(
    ItemMixin,
    study_views.CheckStudyCreatorMixin,
    contrib_views.LeaveWarningMixin,
    study_views.DisableFormIfStudyActiveMixin,
    contrib_views.PaginationHelperMixin,
    generic.TemplateView
):
    title = 'Customize item questions'
    template_name = 'lrex_contrib/crispy_formset_form.html'
    formset = None
    helper = None

    def dispatch(self, request, *args, **kwargs):
        self.n_questions = len(self.study.questions)
        self.helper = forms.itemquestion_formset_helper()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.formset = forms.itemquestion_formset_factory(self.n_questions)(
            queryset=models.ItemQuestion.objects.filter(item=self.item),
        )
        forms.initialize_with_questions(self.formset, self.study.questions)
        if self.n_questions == 0:
            msg = 'Note: If you want to use per item question customization, please ' \
                  '<a href="{}">define the study question</a> first.'.format(
                        reverse('study-questions', args=[self.study.slug]))
            messages.info(self.request, mark_safe(msg))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'reset' in request.POST:
            self.item.itemquestion_set.all().delete()
            return self.get(request, *args, **kwargs)
        self.formset = forms.itemquestion_formset_factory(self.n_questions)(request.POST, request.FILES)
        if self.formset.is_valid():
            instances = self.formset.save(commit=False)
            scale_labels_valid = True
            for instance in instances:
                question = next(question for question in self.study.questions if question.number == instance.number)
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
                messages.success(request, 'Item questions saved.')
                if 'submit' in request.POST:
                    return self.redirect_paginated('items', materials_slug=self.materials.slug)
                else:  # save
                    return self.redirect_paginated('item-questions', item_slug=self.item.slug)
        return super().get(request, *args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.materials.slug])),
            ('items', self.reverse_paginated('items', args=[self.materials.slug])),
            ('{}-questions'.format(self.item), '')
        ]


class ItemFeedbackUpdateView(
    ItemMixin,
    study_views.CheckStudyCreatorMixin,
    contrib_views.LeaveWarningMixin,
    study_views.DisableFormIfStudyActiveMixin,
    contrib_views.PaginationHelperMixin,
    generic.TemplateView
):
    title = 'Customize item feedback'
    template_name = 'lrex_contrib/crispy_formset_form.html'
    formset = None
    helper = None

    def dispatch(self, request, *args, **kwargs):
        self.helper = forms.itemfeedback_formset_helper()
        self.n_feedback = self.item.itemfeedback_set.count()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        extra = 0 if self.n_feedback > 0 else  1
        self.formset = forms.itemfeedback_formset_factory(extra=extra)(
            queryset=self.item.itemfeedback_set.all(),
        )
        forms.itemfeedback_init_formset(self.formset, self.study)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.formset = forms.itemfeedback_formset_factory()(request.POST, request.FILES)
        n_forms = len(self.formset.forms)
        if self.formset.is_valid():
            instances = self.formset.save(commit=False)
            scale_values_valid = True
            n_instances = len(instances)
            for i, instance in enumerate(instances):
                scale_values = instance.scale_values.split(',')
                if not all(instance.question.is_valid_scale_value(scale_value) for scale_value in scale_values):
                    form_num = n_forms - n_instances
                    self.formset._errors[form_num]['scale_values'] = \
                        self.formset.error_class(ValidationError('Invalid scale values').error_list)
                    scale_values_valid = False
                    break
                instance.item = self.item
            if scale_values_valid:
                for instance in instances:
                    instance.save()
            self.n_feedback = self.item.itemfeedback_set.count()
            extra = n_forms - self.n_feedback
            if 'submit' in request.POST:
                if scale_values_valid:
                    messages.success(request, 'Feedback saved.')
                    return self.redirect_paginated('items', materials_slug=self.materials.slug)
            elif 'save' in request.POST:
                if scale_values_valid:
                    messages.success(request, 'Feedback saved.')
                    return self.redirect_paginated('item-feedback', item_slug=self.item.slug)
            elif 'add' in request.POST:
                self.formset = forms.itemfeedback_formset_factory(extra + 1)(
                    queryset=self.item.itemfeedback_set.all(),
                )
            else: # delete last
                if extra > 0:
                    extra -= 1
                elif self.n_feedback > 0:
                    self.item.itemfeedback_set.last().delete(),
                    self.n_feedback -= 1
                self.formset = forms.itemfeedback_formset_factory(extra)(
                    queryset=self.item.itemfeedback_set.all(),
                )
            forms.itemfeedback_init_formset(self.formset, self.study)
        return super().get(request, *args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.materials.slug])),
            ('items', self.reverse_paginated('items', args=[self.materials.slug])),
            ('{}-feedback'.format(self.item),'')
        ]


class ItemFeedbackUploadView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    contrib_views.PaginationHelperMixin,
    generic.FormView
):
    title = 'Upload item feedback'
    form_class = forms.ItemFeedbackUploadForm
    template_name = 'lrex_contrib/crispy_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['materials'] = self.materials
        return kwargs

    def form_valid(self, form):
        result = super().form_valid(form)
        columns = {
            'item_number': form.cleaned_data['item_number_column'] - 1,
            'item_condition': form.cleaned_data['item_condition_column'] - 1,
            'question': form.cleaned_data['question_column'] - 1,
            'scale_values': form.cleaned_data['scale_values_column'] - 1,
            'feedback': form.cleaned_data['feedback_column'] - 1,
        }
        data = StringIO(contrib_csv.read_file(form.cleaned_data))
        self.materials.item_feedbacks_csv_create(data, has_materials_column=False, user_columns=columns, detected_csv=form.detected_csv)
        messages.success(self.request, 'Item lists uploaded.')
        return result

    def get_success_url(self):
        return self.reverse_paginated('items', args=[self.materials.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.materials.slug])),
            ('items', self.reverse_paginated('items', args=[self.materials.slug])),
            ('upload-feedback', ''),
        ]

class ItemCSVDownloadView(materials_views.MaterialsMixin, study_views.CheckStudyCreatorMixin, generic.View):

    def get(self, request, *args, **kwargs):
        filename = '{}_{}_ITEMS_{}.csv'.format(
            self.study.title.replace(' ', '_'), self.materials.title.replace(' ', '_'), str(now().date())
        )
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        self.materials.items_csv(response)
        return response


class ItemListListView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    contrib_views.ActionsMixin,
    materials_views.MaterialsNavMixin,
    generic.ListView
):
    model = models.ItemList
    secondary_nav_active = 1

    @property
    def title(self):
        return '{}: Item lists'.format(self.materials.title)

    def get_queryset(self):
        return models.ItemList.objects.filter(materials=self.materials)

    @property
    def is_disabled(self):
        return self.materials.items_validated

    @property
    def actions(self):
        return [
            ('button', 'Validate / generate lists', 'validate', self.ACTION_CSS_BUTTON_PRIMARY),
        ]

    @property
    def secondary_actions(self):
        return [
            ('link', 'Upload CSV', reverse('itemlist-upload', args=[self.materials.slug])),
            ('link', 'Download CSV', reverse('itemlist-download', args=[self.materials.slug])),
            ('link', 'Delete materials', reverse('materials-delete', args=[self.materials.slug])),
        ]

    @property
    def disable_actions(self):
        if self.is_disabled:
            return [1], [0]

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.materials.slug])),
            ('itemlists', ''),
        ]


class ItemListUploadView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    generic.FormView
):
    title = 'Upload custom item lists'
    form_class = forms.ItemListUploadForm
    template_name = 'lrex_contrib/crispy_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['materials'] = self.materials
        return kwargs

    def form_valid(self, form):
        result = super().form_valid(form)
        self.materials.itemlist_set.all().delete()
        columns = {
            'list': form.cleaned_data['list_column'] - 1,
            'items': form.cleaned_data['items_column'] - 1,
        }
        data = StringIO(contrib_csv.read_file(form.cleaned_data))
        self.materials.itemlists_csv_create(data, has_materials_column=False, user_columns=columns, detected_csv=form.detected_csv)
        messages.success(self.request, 'Item lists uploaded.')
        return result

    def get_success_url(self):
        return reverse('itemlists', args=[self.materials.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.materials.slug])),
            ('itemlists', reverse('itemlists', args=[self.materials.slug])),
            ('upload', ''),
        ]


class ItemListCSVDownloadView(materials_views.MaterialsMixin, study_views.CheckStudyCreatorMixin, generic.View):

    def get(self, request, *args, **kwargs):
        filename = '{}_{}_LISTS_{}.csv'.format(
            self.study.title.replace(' ', '_'), self.materials.title.replace(' ', '_'), str(now().date())
        )
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        self.materials.itemlists_csv(response)
        return response
