from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import generic

from apps.setup import models as setup_models

from . import models


class BinaryResponseInfoView(LoginRequiredMixin, generic.RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        setup = setup_models.Setup.objects.get(slug=setup_slug)
        try:
            response_info = models.BinaryResponseInfo.objects.get(setup=setup)
            return reverse('binary-response-info-update', args=[setup.slug, response_info.pk])
        except models.BinaryResponseInfo.DoesNotExist:
            return reverse('binary-response-info-create', args=[setup.slug])


class BinaryResponseInfoCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.BinaryResponseInfo
    fields = ['question', 'legend', 'yes', 'no']
    title = 'Set Response Info'

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


class BinaryResponseInfoUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = models.BinaryResponseInfo
    fields = ['question', 'legend', 'yes', 'no']
    title = 'Set Response Info'

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
