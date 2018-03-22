from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from apps.study import models as study_models

from . import forms
from . import models


class QuestionnaireListView(LoginRequiredMixin, generic.ListView):
    model = models.Questionnaire
    title = 'Questionnaires'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'generate_questionnaires':
            self.study.generate_questionnaires()
        return redirect('questionnaires',study_slug=self.study.slug)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('questionnaires', ''),
        ]


class TrialCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Trial
    form_class = forms.TrialForm

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['study'] = self.study
        return kwargs

    def _trial_by_id(self, id):
        if id:
            try:
                return models.Trial.objects.get(id=id)
            except models.Trial.DoesNotExist:
                pass
        return None

    def form_valid(self, form):
        active_trial = self._trial_by_id(form.instance.id)
        if active_trial:
            return redirect('user-response-intro', self.study.slug, active_trial.slug)
        form.instance.study = self.study
        form.instance.init()
        response = super().form_valid(form)
        form.instance.generate_items()
        return response

    def get_success_url(self):
        return reverse('user-response-intro', args=[self.study.slug, self.object.slug])


class TrialListView(LoginRequiredMixin, generic.ListView):
    model = models.Trial
    title = 'Trials'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study-run', args=[self.study.slug])),
            ('trials', ''),
        ]


class TrialDetailView(LoginRequiredMixin, generic.DetailView):
    model = models.Trial
    title = 'Trial Overview'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study-run', args=[self.study.slug])),
            ('trials', reverse('trials', args=[self.study.slug])),
            (self.object.pk, ''),
        ]

class TrialDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = models.Trial
    title = 'Delete'
    message = 'Delete Trial?'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.object.slug, reverse('study', args=[self.object.slug])),
            ('delete', ''),
        ]

    @property
    def cancel_url(self):
        return reverse('trials', args=[self.study.slug])

    def get_success_url(self):
        return reverse('trials', args=[self.study.slug])
