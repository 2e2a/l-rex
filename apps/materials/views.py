from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
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


class MaterialsNavMixin(study_views.StudyNavMixin):
    nav_active = 3

    @property
    def materials_nav(self):
        return super().materials_nav

    @property
    def secondary_nav(self):
        return [
            ('link', ('Items', reverse('items', args=[self.materials.slug]))),
            ('link', ('Lists', reverse('itemlists', args=[self.materials.slug]))),
            ('link', ('Settings', reverse('materials-update', args=[self.materials.slug]))),
        ]


class MaterialsCreateView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    study_views.StudyNavMixin,
    generic.CreateView
):
    model = models.Materials
    title = 'Create materials'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.MaterialsForm
    success_message = 'Materials created.'
    nav_active = 3

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
            ('create materials','')
        ]


class MaterialsUpdateView(
    MaterialsObjectMixin,
    study_views.CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contrib_views.LeaveWarningMixin,
    contrib_views.ActionsMixin,
    study_views.DisableFormIfStudyActiveMixin,
    MaterialsNavMixin,
    generic.UpdateView
):
    model = models.Materials
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.MaterialsUpdateForm
    success_message = 'Materials successfully updated.'
    secondary_nav_active = 2

    @property
    def title(self):
        return '{}: Settings'.format(self.materials.title)

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
    def actions(self):
        return [
            ('link', 'Delete materials', reverse('materials-delete', args=[self.materials.slug]), self.ACTION_CSS_BUTTON_DANGER)
        ]

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            (self.materials.title, reverse('materials', args=[self.object.slug])),
            ('edit','')
        ]


class MaterialsView(MaterialsMixin, generic.RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        return reverse('items', args=[self.materials.slug])


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
            (self.materials.title, reverse('materials', args=[self.object.slug])),
            ('delete','')
        ]

    def get_success_url(self):
        return reverse('study', args=[self.study.slug])


class ResultsNavMixin(study_views.StudyNavMixin):
    nav_active = 6

    @property
    def materials_results_nav(self):
        return [
            (materials.title, reverse('materials-results', args=[materials.slug]))
            for materials in self.study.materials_list
        ]

    @property
    def secondary_nav(self):
        return [
            ('link', ('Trials', reverse('trials', args=[self.study.slug]))),
            ('dropdown', ('Summery', self.materials_results_nav)),
        ]


class MaterialsResultsView(
    MaterialsObjectMixin,
    study_views.CheckStudyCreatorMixin,
    contrib_views.ActionsMixin,
    ResultsNavMixin,
    generic.DetailView
):
    model = models.Materials
    template_name = 'lrex_materials/materials_results.html'
    aggregate_by = ['subject']
    aggregate_by_label = 'subject'
    page = 1
    paginate_by = 16
    secondary_nav_active = 1

    @property
    def title(self):
        return 'Results: {}'.format(self.materials.title)

    def dispatch(self, request, *args, **kwargs):
        self.page = request.GET.get('page')
        aggregate_by = request.GET.get('aggregate_by')
        if aggregate_by:
            self.aggregate_by = aggregate_by.split(',')
            self.aggregate_by_label = '+'.join(self.aggregate_by)
        return super().dispatch(request, *args, **kwargs)

    def _aggregated_results(self):
        results = self.object.aggregated_results(self.aggregate_by)
        paginator = Paginator(results, self.paginate_by)
        results_on_page = paginator.get_page(self.page)
        return results_on_page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'results': self._aggregated_results(),
            'aggregate_by': self.aggregate_by,
            'aggregate_by_label': self.aggregate_by_label,
            'aggregate_by_url_par': 'aggregate_by=' + ','.join(self.aggregate_by),
        })
        return context

    @property
    def actions(self):
        aggregate_action = (
            'dropdown',
            'aggregateBy',
            'Aggregated by: {}'.format(self.aggregate_by_label),
            [
                ('subject', '?aggregate_by=subject'),
                ('item', '?aggregate_by=item'),
                ('subject+item', '?aggregate_by=subject,item')
            ],
            self.ACTION_CSS_BUTTON_PRIMARY
        )
        return [
            ('link', 'Results CSV', reverse('study-results-csv', args=[self.study.slug]), self.ACTION_CSS_BUTTON_SECONDARY),
            aggregate_action,
        ]

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study',args=[self.study.slug])),
            ('results', reverse('trials',args=[self.study.slug])),
            (self.materials.title,'')
        ]
