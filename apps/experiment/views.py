from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.urls import reverse
from django.views import generic

from apps.contrib import views as contrib_views
from apps.study import models as study_models
from apps.study import views as study_views

from . import forms
from . import models


class ExperimentDetailView(LoginRequiredMixin, study_views.NextStepsMixin, generic.DetailView):
    model = models.Experiment
    title = 'Experiment Overview'

    @property
    def study(self):
        return self.object.study

    @property
    def experiment(self):
        return self.object

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            (self.object.title, '')
        ]


class ExperimentCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Experiment
    title = 'Create Experiment'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.ExperimentForm

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.study = self.study
        response = super().form_valid(form)
        self.study.set_progress(self.study.PROGRESS_STD_EXP_CREATED)
        messages.success(self.request, study_views.progress_success_message(self.study.progress))
        return response

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('experiments',reverse('experiments', args=[self.study.slug])),
            ('create','')
        ]


class ExperimentUpdateView(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = models.Experiment
    title = 'Edit Experiment'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.ExperimentForm
    success_message = 'Experiment successfully updated.'

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.object.study.title, reverse('study', args=[self.object.study.slug])),
            ('experiments',reverse('experiments', args=[self.object.study.slug])),
            (self.object.title, reverse('experiment', args=[self.object.study.slug, self.object.slug])),
            ('edit','')
        ]


class ExperimentDeleteView(LoginRequiredMixin, contrib_views.DefaultDeleteView):
    model = models.Experiment

    def delete(self, *args, **kwargs):
        response = super().delete(*args, **kwargs)
        study = self.object.study
        if not models.Experiment.objects.filter(study=study).exists():
            study.set_progress(study.PROGRESS_STD_SCALE_CONFIGURED)
        return response

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.object.study.title, reverse('study', args=[self.object.study.slug])),
            ('experiments',reverse('experiments', args=[self.object.study.slug])),
            (self.object.title, reverse('experiment', args=[self.object.study.slug, self.object.slug])),
            ('delete','')
        ]

    def get_success_url(self):
        return reverse('experiments', args=[self.object.study.slug])


class ExperimentListView(LoginRequiredMixin, study_views.NextStepsMixin, generic.ListView):
    model = models.Experiment
    title = 'Experiments'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(study=self.study)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study',args=[self.study.slug])),
            ('experiments','')
        ]


class ExperimentResultListView(LoginRequiredMixin, generic.ListView):
    model = models.Experiment
    title = 'Experiment Results'
    template_name = 'lrex_experiment/experiment_result_list.html'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(study=self.study)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study-run',args=[self.study.slug])),
            ('results','')
        ]


class ExperimentResultsView(LoginRequiredMixin, generic.DetailView):
    model = models.Experiment
    title = 'Experiment Results'
    template_name = 'lrex_experiment/experiment_results.html'
    aggregate_by = ['subject']
    page = 1
    paginate_by = 16

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
        results = self.object.results()
        results = self.object.aggregate(results, self.aggregate_by)
        paginator = Paginator(results, self.paginate_by)
        results_on_page = paginator.get_page(self.page)
        return results_on_page

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['results'] = self._aggregated_results()
        return data


    @property
    def study(self):
        return self.object.study

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study-run',args=[self.study.slug])),
            ('results', reverse('experiment-result-list',args=[self.study.slug])),
            (self.object.title,'')
        ]


class ExperimentResultsCSVDownloadView(generic.View):

    def dispatch(self, *args, **kwargs):
        experiment_slug = self.kwargs['slug']
        self.experiment = models.Experiment.objects.get(slug=experiment_slug)
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        filename = self.experiment.slug + '.csv'
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        self.experiment.results_csv(response)
        return response
