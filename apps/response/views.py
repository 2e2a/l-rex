from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import generic

from apps.setup import models as setup_models
from apps.trial import models as trail_models

from . import forms
from . import models


class BinaryResponseSettingsView(LoginRequiredMixin, generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        setup = setup_models.Setup.objects.get(slug=setup_slug)
        try:
            response_info = models.BinaryResponseSettings.objects.get(setup=setup)
            return reverse('binary-response-info-update', args=[setup.slug, response_info.pk])
        except models.BinaryResponseSettings.DoesNotExist:
            return reverse('binary-response-info-create', args=[setup.slug])


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


class UserResponseIntroView(generic.TemplateView):
    template_name = 'lrex_response/userresponseintro.html'

    def dispatch(self, *args, **kwargs):
        user_trial_slug = self.kwargs['slug']
        self.user_trial = trail_models.UserTrial.objects.get(slug=user_trial_slug)
        self.setup = self.user_trial.trial.setup
        return super().dispatch(*args, **kwargs)


class UserResponseOutroView(generic.TemplateView):
    template_name = 'lrex_response/userresponseoutro.html'

    def dispatch(self, *args, **kwargs):
        user_trial_slug = self.kwargs['slug']
        self.user_trial = trail_models.UserTrial.objects.get(slug=user_trial_slug)
        self.setup = self.user_trial.trial.setup
        return super().dispatch(*args, **kwargs)


class UserBinaryResponseCreateView(generic.CreateView):
    model = models.UserBinaryResponse
    form_class = forms.UserBinaryResponseForm

    def dispatch(self, *args, **kwargs):
        user_trial_slug = self.kwargs['slug']
        self.num = int(self.kwargs['num'])
        self.user_trial = trail_models.UserTrial.objects.get(slug=user_trial_slug)
        self.user_trial_item = trail_models.UserTrialItem.objects.get(
            user_trial__slug=user_trial_slug,
            number=self.num
        )
        self.setup = self.user_trial.trial.setup
        self.yes = self.setup.responseinfo.binaryresponseinfo.yes
        self.no = self.setup.responseinfo.binaryresponseinfo.no
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.number = self.num
        form.instance.user_trial_item = self.user_trial_item
        return super().form_valid(form)

    def get_success_url(self):
        if self.num < (len(self.user_trial.items) - 1):
            return reverse('user-binary-response', args=[self.setup.slug, self.user_trial.slug, self.num + 1])
        return reverse('user-response-outro', args=[self.setup.slug, self.user_trial.slug])
