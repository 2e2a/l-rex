from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import generic

from apps.setup import models as setup_models

from . import models


class BinaryResponseInfoDetailView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'lrex_responseinfo/binaryresponseinfo_detail.html'
    title = 'Response Info'

    def dispatch(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        self.setup = setup_models.Setup.objects.get(slug=setup_slug)
        try:
            self.object = models.BinaryResponseInfo.objects.get(setup=self.setup)
        except models.BinaryResponseInfo.DoesNotExist:
            pass
        return super().dispatch(*args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('setups', reverse('setups')),
            (self.setup.title, reverse('setup', args=[self.setup.slug])),
            ('response','')
        ]


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
        return reverse('binary-response-info', args=[self.setup.slug])

    @property
    def breadcrumbs(self):
        return [
            ('setups', reverse('setups')),
            (self.setup.title, reverse('setup', args=[self.setup.slug])),
            ('response', reverse('binary-response-info', args=[self.setup.slug])),
            ('create','')
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
        return reverse('binary-response-info', args=[self.setup.slug])

    @property
    def breadcrumbs(self):
        return [
            ('setups', reverse('setups')),
            (self.setup.title, reverse('setup', args=[self.setup.slug])),
            ('response', reverse('binary-response-info', args=[self.setup.slug])),
            ('edit','')
        ]
