from io import StringIO
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
from apps.contrib.utils import split_list_string
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
        return self.item.materials

    @property
    def item(self):
        if not self.item_object:
            item_slug = self.kwargs['item_slug']
            self.item_object = models.Item.objects.get(slug=item_slug)
        return self.item_object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'study': self.study,
            'materials': self.materials,
            'item': self.item,
        })
        return context


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
            for warning in warnings:
                messages.warning(self.request, '{}'.format(warning))
            messages.success(self.request, 'Items seem valid. Lists automatically generated.')
            if self.study.has_questionnaires:
                self.study.delete_questionnaires()
                messages.info(self.request, 'Old questionnaires deleted.')
            return True
        except AssertionError as e:
            messages.error(self.request, str(e))
        return False


class ItemListView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    study_views.MaterialsNavMixin,
    ItemsValidateMixin,
    generic.ListView
):
    model = models.Item
    paginate_by = 16
    title = 'Items'

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'validate':
            if self.validate_items():
                return redirect('itemlists', materials_slug=self.materials.slug)
        return redirect('items', materials_slug=self.materials.slug)

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(materials=self.materials)
        queryset = queryset.prefetch_related(
            'materials',
        )
        if self.study.has_text_items:
            queryset = queryset.prefetch_related('textitem')
        elif self.study.has_markdown_items:
            queryset = queryset.prefetch_related('markdownitem')
        elif self.study.has_audiolink_items:
            queryset = queryset.prefetch_related('audiolinkitem')
        return queryset


class ItemCreateMixin(contrib_views.PaginationHelperMixin):
    template_name = 'lrex_dashboard/materials_form.html'
    title = 'Add new item'

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


class ItemUpdateMixin(
    contrib_views.LeaveWarningMixin,
    contrib_views.PaginationHelperMixin,
    study_views.MaterialsNavMixin,
):
    template_name = 'lrex_dashboard/materials_form.html'
    success_message = 'Item successfully updated.'
    title = 'Edit item'

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


class ItemCreateView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    generic.base.RedirectView
):

    def get_redirect_url(self, *args, **kwargs):
        if self.study.has_text_items:
            url = reverse('text-item-create', args=[self.materials.slug])
        elif self.study.has_markdown_items:
            url = reverse('markdown-item-create', args=[self.materials.slug])
        else:
            url = reverse('audio-link-item-create', args=[self.materials.slug])
        page = kwargs.get('page', None)
        if page:
            url += '?page={}'.format(page)
        return url


class ItemUpdateView(
    ItemMixin,
    study_views.CheckStudyCreatorMixin,
    generic.base.RedirectView
):

    def get_redirect_url(self, *args, **kwargs):
        if self.study.has_text_items:
            url = reverse('text-item-update', args=[self.item.slug])
        elif self.study.has_markdown_items:
            url = reverse('markdown-item-update', args=[self.item.slug])
        else:
            url = reverse('audio-link-item-update', args=[self.item.slug])
        page = kwargs.get('page', None)
        if page:
            url += '?page={}'.format(page)
        return url


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
    contrib_views.DefaultDeleteView
):
    model = models.Item
    template_name = 'lrex_dashboard/materials_confirm_delete.html'

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        self.materials.set_items_validated(False)
        self.materials.delete_lists()
        return result

    def get_success_url(self):
        return self.reverse_paginated('items', args=[self.materials.slug])


class ItemPregenerateView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    SuccessMessageMixin,
    study_views.DisableFormIfStudyActiveMixin,
    contrib_views.PaginationHelperMixin,
    study_views.MaterialsNavMixin,
    generic.FormView
):
    form_class = forms.PregenerateItemsForm
    template_name = 'lrex_dashboard/materials_form.html'
    success_message = 'Items successfully generated.'
    title = 'Pregenerate items'

    def form_valid(self, form):
        result =  super().form_valid(form)
        n_items = form.cleaned_data['num_items']
        n_conditions = form.cleaned_data['num_conditions']
        models.Item.objects.filter(materials=self.materials).delete()
        self.materials.pregenerate_items(n_items, n_conditions)
        return result

    def get_success_url(self):
        return self.reverse_paginated('items', args=[self.materials.slug])


class ItemUploadView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    ItemsValidateMixin,
    study_views.DisableFormIfStudyActiveMixin,
    study_views.MaterialsNavMixin,
    generic.FormView
):
    form_class = forms.ItemUploadForm
    template_name = 'lrex_dashboard/materials_form.html'
    title = 'Upload items'

    def dispatch(self, request, *args, **kwargs):
        if not self.study.questions.exists():
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
        questions = list(self.study.questions.all())
        columns = {
            'item': form.cleaned_data['number_column'] - 1,
            'condition': form.cleaned_data['condition_column'] - 1,
            'content': form.cleaned_data['content_column'] - 1,
        }
        if form.cleaned_data['block_column'] > 0:
            columns.update({'block': form.cleaned_data['block_column'] - 1})
        if self.study.has_audiolink_items:
            if form.cleaned_data['audio_description_column'] > 0:
                columns.update({'audio_description': form.cleaned_data['audio_description_column'] - 1})
        for i, question in enumerate(questions):
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
        self.materials.items_from_csv(
            data, has_materials_column=False, user_columns=columns, detected_csv=form.detected_csv,
        )
        messages.success(self.request, 'Items uploaded.')
        self.validate_items()
        return result

    def get_success_url(self):
        return reverse('items', args=[self.materials.slug])


class ItemDeleteAllView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    study_views.MaterialsNavMixin,
    generic.TemplateView
):
    title = 'Confirm deletion'
    template_name = 'lrex_dashboard/materials_confirm_delete.html'
    message = 'Delete all items?'

    def post(self, request, *args, **kwargs):
        models.Item.objects.filter(materials=self.materials).delete()
        self.materials.set_items_validated(False)
        self.materials.delete_lists()
        messages.success(self.request, 'All items deleted.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('items', args=[self.materials.slug])


class ItemQuestionsUpdateView(
    ItemMixin,
    study_views.CheckStudyCreatorMixin,
    contrib_views.LeaveWarningMixin,
    study_views.DisableFormIfStudyActiveMixin,
    contrib_views.PaginationHelperMixin,
    study_views.MaterialsNavMixin,
    contrib_views.FormsetView
):
    template_name = 'lrex_dashboard/materials_formset_form.html'
    formset = None
    helper = None
    formset_factory = forms.ItemQuestionFormsetFactory
    custom_formset = forms.ItemQuestionFormset

    @property
    def title(self):
        return 'Customize item {} questions'.format(self.item)

    def get_formset_queryset(self):
        return self.item.item_questions.all()

    def get_form_count(self):
        return self.study.questions.count()

    def save_form(self, form, number):
        form.instance.item = self.item
        super().save_form(form, number)

    def submit_redirect(self):
        return self.redirect_paginated('items', materials_slug=self.materials.slug)

    def get(self, request, *args, **kwargs):
        if self.get_form_count() == 0:
            msg = (
                'Note: If you want to use per item question customization, please '
                  '<a href="{}">define the study question</a> first.'
            ).format(reverse('study-questions', args=[self.study.slug]))
            messages.info(self.request, mark_safe(msg))
        return super().get(request, *args, **kwargs)


class ItemFeedbackUpdateView(
    ItemMixin,
    study_views.CheckStudyCreatorMixin,
    contrib_views.LeaveWarningMixin,
    study_views.DisableFormIfStudyActiveMixin,
    contrib_views.PaginationHelperMixin,
    study_views.MaterialsNavMixin,
    contrib_views.FormsetView
):
    template_name = 'lrex_dashboard/materials_formset_form.html'
    formset = None
    helper = None
    formset_factory = forms.ItemFeedbackFormsetFactory

    @property
    def title(self):
        return 'Define item {} feedback'.format(self.item)

    def get_formset_queryset(self):
        return self.item.item_feedback.all()

    def save_form(self, form, number):
        form.instance.item = self.item
        super().save_form(form, number)

    def submit_redirect(self):
        return self.redirect_paginated('items', materials_slug=self.materials.slug)


class ItemFeedbackUploadView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    contrib_views.PaginationHelperMixin,
    study_views.MaterialsNavMixin,
    generic.FormView
):
    form_class = forms.ItemFeedbackUploadForm
    template_name = 'lrex_dashboard/materials_form.html'
    title = 'Upload item feedback'

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
        self.materials.item_feedbacks_from_csv(data, has_materials_column=False, user_columns=columns, detected_csv=form.detected_csv)
        messages.success(self.request, 'Item lists uploaded.')
        return result

    def get_success_url(self):
        return self.reverse_paginated('items', args=[self.materials.slug])


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
    ItemsValidateMixin,
    study_views.MaterialsNavMixin,
    generic.ListView
):
    model = models.ItemList
    title = 'Item lists'

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'validate':
            self.validate_items()
        return redirect('itemlists', materials_slug=self.materials.slug)

    def get_queryset(self):
        queryset = models.ItemList.objects.filter(materials=self.materials)
        queryset = queryset.prefetch_related('items')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'nav2_active': 1,
        })
        return context


class ItemListUploadView(
    materials_views.MaterialsMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    study_views.MaterialsNavMixin,
    generic.FormView
):
    form_class = forms.ItemListUploadForm
    template_name = 'lrex_dashboard/materials_form.html'
    title = 'Upload item lists'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'nav2_active': 1,
        })
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['materials'] = self.materials
        return kwargs

    def form_valid(self, form):
        result = super().form_valid(form)
        self.materials.lists.all().delete()
        columns = {
            'list': form.cleaned_data['list_column'] - 1,
            'items': form.cleaned_data['items_column'] - 1,
        }
        data = StringIO(contrib_csv.read_file(form.cleaned_data))
        self.materials.itemlists_from_csv(data, has_materials_column=False, user_columns=columns, detected_csv=form.detected_csv)
        messages.success(self.request, 'Item lists uploaded.')
        return result

    def get_success_url(self):
        return reverse('itemlists', args=[self.materials.slug])


class ItemListCSVDownloadView(materials_views.MaterialsMixin, study_views.CheckStudyCreatorMixin, generic.View):

    def get(self, request, *args, **kwargs):
        filename = '{}_{}_LISTS_{}.csv'.format(
            self.study.title.replace(' ', '_'), self.materials.title.replace(' ', '_'), str(now().date())
        )
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        self.materials.itemlists_csv(response)
        return response
