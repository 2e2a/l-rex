from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views import generic

from apps.contrib import views as contrib_views
from apps.study import views as study_views

from . import forms
from . import models


class MaterialsMixin:
    materials_object = None
    slug_url_kwarg = 'materials_slug'

    @property
    def study(self):
        return self.materials.study

    @property
    def materials(self):
        if not self.materials_object:
            materials_slug = self.kwargs['materials_slug']
            self.materials_object = models.Materials.objects.get(slug=materials_slug)
        return self.materials_object

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['study'] = self.study
        data['materials'] = self.materials
        return data


class MaterialsObjectMixin(MaterialsMixin):

    @property
    def materials(self):
        if not self.materials_object:
            self.materials_object =  self.get_object()
        return self.materials_object


class MaterialsListView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.NextStepsMixin,
    generic.ListView
):
    model = models.Materials
    title = 'Materials'

    def get_queryset(self):
        return super().get_queryset().filter(study=self.study)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study',args=[self.study.slug])),
            ('materials', '')
        ]


class MaterialsCreateView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    generic.CreateView
):
    model = models.Materials
    title = 'Create materials'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.MaterialsForm
    success_message = 'Materials created.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['study'] = self.study
        return kwargs

    def form_valid(self, form):
        form.instance.study = self.study
        response = super().form_valid(form)
        return response

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('materials',reverse('materials-list', args=[self.study.slug])),
            ('create','')
        ]


class MaterialsDetailView(
    MaterialsObjectMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.NextStepsMixin,
    generic.DetailView
):
    model = models.Materials

    @property
    def title(self):
        return self.materials.title

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['items_validated'] = self.materials.items_validated
        return data

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('materials',reverse('materials-list', args=[self.study.slug])),
            (self.materials.title, '')
        ]


class MaterialsUpdateView(
    MaterialsObjectMixin,
    study_views.CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contrib_views.LeaveWarningMixin,
    study_views.DisableFormIfStudyActiveMixin,
    generic.UpdateView
):
    model = models.Materials
    title = 'Edit Materials'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.MaterialsUpdateForm
    success_message = 'Materials successfully updated.'

    def get(self, request, *args, **kwargs):
        if self.study.has_questionnaires:
            msg = 'Note: To change the block related settings you would need ' \
                  '<a href="{}">to remove questionnaires first</a>.'.format(
                    reverse('questionnaires', args=[self.study.slug]))
            messages.info(request, mark_safe(msg))
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['study'] = self.study
        kwargs['disable_list_settings'] = self.study.has_questionnaires
        kwargs['disable_block_settings'] = self.study.has_questionnaires
        return kwargs

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('materials',reverse('materials-list', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.object.slug])),
            ('edit','')
        ]


class MaterialsDeleteView(
    MaterialsObjectMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    contrib_views.DefaultDeleteView
):
    model = models.Materials

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('materials',reverse('materials-list', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.object.slug])),
            ('delete','')
        ]

    def get_success_url(self):
        return reverse('materials-list', args=[self.study.slug])


class MaterialsResultListView(study_views.StudyMixin, study_views.CheckStudyCreatorMixin, generic.ListView):
    model = models.Materials
    title = 'Results'
    template_name = 'lrex_materials/materials_result_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(study=self.study)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study',args=[self.study.slug])),
            ('results','')
        ]


class MaterialsResultsView(MaterialsObjectMixin, study_views.CheckStudyCreatorMixin, generic.DetailView):
    model = models.Materials
    title = 'Results'
    template_name = 'lrex_materials/materials_results.html'
    aggregate_by = ['subject']
    page = 1
    paginate_by = 16

    @staticmethod
    def clear_cache(materials):
        cache.delete_many([
            '{}-results-subj'.format(materials.slug),
            '{}-results-subj-item'.format(materials.slug),
        ])

    def _cache_key_results(self):
        if self.aggregate_by == ['subject']:
            return '{}-results-subj'.format(self.materials.slug)
        else:
            return '{}-results-subj-item'.format(self.materials.slug)

    def dispatch(self, request, *args, **kwargs):
        self.page = request.GET.get('page')
        aggregate_by = request.GET.get('aggregate_by')
        if aggregate_by:
            self.aggregate_by = aggregate_by.split(',')
        return super().dispatch(request, *args, **kwargs)

    def aggregate_by_subject_url_par(self):
        return 'aggregate_by=subject'

    def aggregate_by_subject_and_item_url_par(self):
        return 'aggregate_by=subject,item'

    def aggregate_by_label(self):
        return '+'.join(self.aggregate_by)

    def aggregate_by_url_par(self):
        return 'aggregate_by=' + ','.join(self.aggregate_by)

    def _aggregated_results(self):
        results = self.object.aggregated_results(self.aggregate_by)
        paginator = Paginator(results, self.paginate_by)
        results_on_page = paginator.get_page(self.page)
        return results_on_page

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['results'] = self._aggregated_results()
        return data

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study',args=[self.study.slug])),
            ('results', reverse('materials-result-list',args=[self.study.slug])),
            (self.materials.title,'')
        ]


class MaterialsResultsCSVDownloadView(MaterialsObjectMixin, study_views.CheckStudyCreatorMixin, generic.DetailView):
    model = models.Materials

    def get(self, request, *args, **kwargs):
        filename = '{}_RESULTS_{}.csv'.format(self.materials.title.replace(' ', '_'), str(now().date()))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        self.materials.results_csv(response)
        return response
