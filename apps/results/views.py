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
            if self.trial.status == trial_models.TrialStatus.FINISHED:
                return reverse('user-response-taken', args=[self.study.slug, self.trial.slug])
            n_responses = len(models.UserResponse.objects.filter(trial_item__trial=self.trial))
            return reverse('user-binary-response', args=[self.study.slug, self.trial.slug, n_responses])
        except models.UserResponse.DoesNotExist:
            pass
        except trial_models.TrialItem.DoesNotExist:
            pass
        return None

    def dispatch(self, *args, **kwargs):
        trial_slug = self.kwargs['slug']
        self.trial = trial_models.Trial.objects.get(slug=trial_slug)
        self.study = self.trial.questionnaire.study
        redirect_link = self._redirect_started()
        if redirect_link:
            return redirect(redirect_link)
        return super().dispatch(*args, **kwargs)


class UserResponseOutroView(generic.TemplateView):
    template_name = 'lrex_results/userresponse_outro.html'

    def dispatch(self, *args, **kwargs):
        trial_slug = self.kwargs['slug']
        self.trial = trial_models.Trial.objects.get(slug=trial_slug)
        self.study = self.trial.questionnaire.study
        return super().dispatch(*args, **kwargs)


class UserResponseTakenView(generic.TemplateView):
    template_name = 'lrex_results/userresponse_taken.html'


class UserResponseCreateView(generic.CreateView):
    model = models.UserResponse
    form_class = forms.UserResponseForm

    def dispatch(self, *args, **kwargs):
        trial_slug = self.kwargs['slug']
        self.num = int(self.kwargs['num'])
        self.trial = trial_models.Trial.objects.get(slug=trial_slug)
        if self.trial.status == trial_models.TrialStatus.FINISHED:
            return redirect(reverse('user-response-taken', args=[self.study.slug, self.trial.slug]))
        self.study = self.trial.questionnaire.study
        self.trial_item = trial_models.TrialItem.objects.get(
            trial__slug=trial_slug,
            number=self.num
        )
        return super().dispatch(*args, **kwargs)

    def progress(self):
        return self.num * 100 / len(self.trial.items)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['study'] = self.study
        return kwargs

    def form_valid(self, form):
        form.instance.number = self.num
        form.instance.trial_item = self.trial_item
        return super().form_valid(form)

    def get_success_url(self):
        if self.num < (len(self.trial.items) - 1):
            return reverse('user-binary-response', args=[self.study.slug, self.trial.slug, self.num + 1])
        return reverse('user-response-outro', args=[self.study.slug, self.trial.slug])
