from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from apps.trial import models as trial_models

from . import forms
from . import models


class UserResponseIntroView(generic.TemplateView):
    template_name = 'lrex_results/userresponse_intro.html'

    def _redirect_started(self):
        try:
            n_responses = len(models.UserResponse.objects.filter(user_trial_item__user_trial=self.user_trial))
            n_user_trial_items = len(trial_models.UserTrialItem.objects.filter(user_trial=self.user_trial))
            if n_responses == n_user_trial_items:
                return reverse('user-response-taken', args=[self.study.slug, self.user_trial.slug])
            return reverse('user-binary-response', args=[self.study.slug, self.user_trial.slug, n_responses])
        except models.UserResponse.DoesNotExist:
            pass
        except trial_models.UserTrialItem.DoesNotExist:
            pass

    def dispatch(self, *args, **kwargs):
        user_trial_slug = self.kwargs['slug']
        self.user_trial = trial_models.UserTrial.objects.get(slug=user_trial_slug)
        self.study = self.user_trial.trial.study
        redirect_link = self._redirect_started()
        if redirect_link:
            return redirect(redirect_link)
        return super().dispatch(*args, **kwargs)


class UserResponseOutroView(generic.TemplateView):
    template_name = 'lrex_results/userresponse_outro.html'

    def dispatch(self, *args, **kwargs):
        user_trial_slug = self.kwargs['slug']
        self.user_trial = trial_models.UserTrial.objects.get(slug=user_trial_slug)
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
        self.user_trial = trial_models.UserTrial.objects.get(slug=user_trial_slug)
        self.study = self.user_trial.trial.study
        self.user_trial_item = trial_models.UserTrialItem.objects.get(
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
