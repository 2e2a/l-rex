from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import generic

from apps.study import models as study_models

from . import models


class BinaryResponseSettingsView(LoginRequiredMixin, generic.RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        study = study_models.Study.objects.get(slug=study_slug)
        try:
            response_settings = models.BinaryResponseSettings.objects.get(study=study)
            return reverse('binary-response-settings-update', args=[study.slug, response_settings.pk])
        except models.BinaryResponseSettings.DoesNotExist:
            return reverse('binary-response-settings-create', args=[study.slug])


class BinaryResponseSettingsCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.BinaryResponseSettings
    fields = ['question', 'legend', 'yes', 'no']
    title = 'Set Response Settings'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.study = self.study
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('study', args=[self.study.slug])

    @property
    def breadcrumbs(self):
        return [
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('response', ''),
        ]


class BinaryResponseSettingsUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = models.BinaryResponseSettings
    fields = ['question', 'legend', 'yes', 'no']
    title = 'Set Response Settings'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.study = self.study
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('study', args=[self.study.slug])

    @property
    def breadcrumbs(self):
        return [
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('response', ''),
        ]
