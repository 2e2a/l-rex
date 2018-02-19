from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from apps.study import models as study_models

from . import models


class TrialListView(LoginRequiredMixin, generic.ListView):
    model = models.Trial
    title = 'Trials'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'generate_trials':
            self.study.generate_trials()
        return redirect('trials',study_slug=self.study.slug)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('trials', ''),
        ]


class UserTrialListView(LoginRequiredMixin, generic.ListView):
    model = models.UserTrial
    title = 'User Trial List'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study-run', args=[self.study.slug])),
            ('user-trials', ''),
        ]


class UserTrialCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.UserTrial
    fields = ['participant']
    title = 'Create User Trial'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.study = self.study
        form.instance.init()
        response = super().form_valid(form)
        form.instance.generate_items()
        return response

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study-run', args=[self.study.slug])),
            ('user-trials', reverse('user-trials', args=[self.study.slug])),
            ('create', ''),
        ]

class UserTrialDetailView(LoginRequiredMixin, generic.DetailView):
    model = models.UserTrial
    title = 'User Trial Overview'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study-run', args=[self.study.slug])),
            ('user-trials', reverse('user-trials', args=[self.study.slug])),
            (self.object.pk, ''),
        ]

class UserTrialDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = models.UserTrial
    title = 'Delete'
    message = 'Delete User Trial?'

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
        return reverse('user-trials', args=[self.study.slug])

    def get_success_url(self):
        return reverse('user-trials', args=[self.study.slug])
