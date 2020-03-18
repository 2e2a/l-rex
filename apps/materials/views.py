from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.views import generic

from apps.contrib import views as contrib_views
from apps.study import views as study_views

from . import forms
from . import models


class MaterialsMixin:
    materials_object = None
    slug_url_kwarg = 'materials_slug'

    @cached_property
    def study(self):
        return self.materials.study

    @cached_property
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

    @cached_property
    def materials(self):
        if not self.materials_object:
            self.materials_object =  self.get_object()
        return self.materials_object


class MaterialsCreateView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    study_views.MaterialsNavMixin,
    generic.CreateView
):
    model = models.Materials
    title = 'Create materials'
    template_name = 'lrex_dashboard/base_form.html'
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

    def get_success_url(self):
        return reverse('items', args=[self.object.slug])


class MaterialsSettingsView(
    MaterialsObjectMixin,
    study_views.CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contrib_views.LeaveWarningMixin,
    study_views.DisableFormIfStudyActiveMixin,
    study_views.MaterialsNavMixin,
    generic.UpdateView
):
    model = models.Materials
    template_name = 'lrex_materials/materials_settings.html'
    form_class = forms.MaterialsSettingsForm
    success_message = 'Materials successfully updated.'
    title = 'Materials settings'

    def get(self, request, *args, **kwargs):
        if not self.is_disabled:
            if self.study.has_questionnaires:
                msg = 'Note: To change the block related settings you would need ' \
                      '<a href="{}">to remove questionnaires first</a>.'.format(
                        reverse('questionnaires', args=[self.study.slug]))
                messages.info(request, mark_safe(msg))
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        if 'save' in self.request.POST:
            return reverse('materials-settings', args=[self.materials.slug])
        return reverse('study', args=[self.study.slug])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'nav2_active': 2,
        })
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'add_save': True,
            'study': self.study,
            'disable_list_settings': self.study.has_questionnaires,
            'disable_block_settings': self.study.has_questionnaires,

        })
        return kwargs


class MaterialsDeleteView(
    MaterialsObjectMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    study_views.MaterialsNavMixin,
    contrib_views.DefaultDeleteView
):
    model = models.Materials
    template_name = 'lrex_dashboard/materials_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'nav2_active': 2,
        })
        return context

    def get_success_url(self):
        return reverse('study', args=[self.study.slug])


class MaterialsResultsView(
    MaterialsObjectMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.ResultsNavMixin,
    contrib_views.PaginationHelperMixin,
    generic.DetailView
):
    model = models.Materials
    template_name = 'lrex_materials/materials_results.html'
    aggregate_by = ['subject', 'item']
    aggregate_by_par = 'subject+item'
    page = 1
    paginate_by = 1
    title = 'Materials result summery'

    def get(self, request, *args, **kwargs):
        self.page = request.GET.get('page', self.page)
        self.aggregate_by_par = request.GET.get('aggregate_by', self.aggregate_by_par)
        self.aggregate_by = self.aggregate_by_par.split()
        return super().get(request, *args, **kwargs)

    def _aggregated_results(self):
        results = self.object.aggregated_results(self.aggregate_by)
        paginator = Paginator(results, self.paginate_by)
        results_on_page = paginator.get_page(self.page)
        return results_on_page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'nav_active': 6,
            'nav2_active': 1,
            'active_materials': self.materials.pk,
            'results': self._aggregated_results(),
            'aggregate_by': self.aggregate_by,
            'aggregate_by_par': self.aggregate_by_par,
        })
        return context
