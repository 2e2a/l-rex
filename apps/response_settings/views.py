from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import generic

from apps.setup import models as setup_models

from . import models


class BinaryResponseSettingsView(LoginRequiredMixin, generic.RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        setup = setup_models.Setup.objects.get(slug=setup_slug)
        try:
            response_settings = models.BinaryResponseSettings.objects.get(setup=setup)
            return reverse('binary-response-settings-update', args=[setup.slug, response_settings.pk])
        except models.BinaryResponseSettings.DoesNotExist:
            return reverse('binary-response-settings-create', args=[setup.slug])


class BinaryResponseSettingsCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.BinaryResponseSettings
    fields = ['question', 'legend', 'yes', 'no']
    title = 'Set Response Settings'

    def dispatch(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        self.setup = setup_models.Setup.objects.get(slug=setup_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.setup = self.setup
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('setup', args=[self.setup.slug])

    @property
    def breadcrumbs(self):
        return [
            ('setups', reverse('setups')),
            (self.setup.title, reverse('setup', args=[self.setup.slug])),
            ('response', ''),
        ]


class BinaryResponseSettingsUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = models.BinaryResponseSettings
    fields = ['question', 'legend', 'yes', 'no']
    title = 'Set Response Settings'

    def dispatch(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        self.setup = setup_models.Setup.objects.get(slug=setup_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.setup = self.setup
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('setup', args=[self.setup.slug])

    @property
    def breadcrumbs(self):
        return [
            ('setups', reverse('setups')),
            (self.setup.title, reverse('setup', args=[self.setup.slug])),
            ('response', ''),
        ]
