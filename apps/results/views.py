from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from apps.trial import models as trail_models

from . import forms
from . import models


class UserResponseIntroView(generic.TemplateView):
    template_name = 'lrex_results/userresponse_intro.html'

    def dispatch(self, *args, **kwargs):
        user_trial_slug = self.kwargs['slug']
        self.user_trial = trail_models.UserTrial.objects.get(slug=user_trial_slug)
        self.study = self.user_trial.trial.study
        if models.UserResponse.objects.filter(user_trial_item__user_trial=self.user_trial).exists():
            return redirect('user-response-taken', self.study.slug, self.user_trial.slug)
        return super().dispatch(*args, **kwargs)


class UserResponseOutroView(generic.TemplateView):
    template_name = 'lrex_results/userresponse_outro.html'

    def dispatch(self, *args, **kwargs):
        user_trial_slug = self.kwargs['slug']
        self.user_trial = trail_models.UserTrial.objects.get(slug=user_trial_slug)
        self.study = self.user_trial.trial.study
        return super().dispatch(*args, **kwargs)


class UserResponseTakenView(generic.TemplateView):
    template_name = 'lrex_results/userresponse_taken.html'


class UserResponseCreateView(generic.CreateView):
    model = models.UserResponse
    form_class = forms.UserResponseForm

    def dispatch(self, *args, **kwargs):
        user_trial_slug = self.kwargs['slug']
        self.num = int(self.kwargs['num'])
        self.user_trial = trail_models.UserTrial.objects.get(slug=user_trial_slug)
        self.study = self.user_trial.trial.study
        self.user_trial_item = trail_models.UserTrialItem.objects.get(
            user_trial__slug=user_trial_slug,
            number=self.num
        )
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['study'] = self.study
        return kwargs

    def form_valid(self, form):
        form.instance.number = self.num
        form.instance.user_trial_item = self.user_trial_item
        return super().form_valid(form)

    def get_success_url(self):
        if self.num < (len(self.user_trial.items) - 1):
            return reverse('user-binary-response', args=[self.study.slug, self.user_trial.slug, self.num + 1])
        return reverse('user-response-outro', args=[self.study.slug, self.user_trial.slug])
