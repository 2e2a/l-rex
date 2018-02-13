from django.urls import reverse
from django.views import generic

from apps.trial import models as trail_models

from . import forms
from . import models


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
        self.yes = self.setup.responsesettings.binaryresponsesettings.yes
        self.no = self.setup.responsesettings.binaryresponsesettings.no
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.number = self.num
        form.instance.user_trial_item = self.user_trial_item
        return super().form_valid(form)

    def get_success_url(self):
        if self.num < (len(self.user_trial.items) - 1):
            return reverse('user-binary-response', args=[self.setup.slug, self.user_trial.slug, self.num+1 ])
        return reverse('user-response-outro', args=[self.setup.slug, self.user_trial.slug ])
