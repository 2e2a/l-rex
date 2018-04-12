from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from apps.contrib import views as contrib_views
from apps.study import models as study_models
from apps.study import views as study_views

from . import forms
from . import models


class QuestionnaireListView(LoginRequiredMixin, study_views.NextStepsMixin, generic.ListView):
    model = models.Questionnaire
    title = 'Questionnaires'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'generate_questionnaires':
            self.study.generate_questionnaires()
            self.study.progress = self.study.PROGRESS_STD_QUESTIONNARES_GENERATED
            self.study.save()
            messages.success(request, study_views.progress_success_message(self.study.progress))
        return redirect('questionnaires',study_slug=self.study.slug)

    def get_queryset(self):
        return super().get_queryset().filter(study=self.study)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('questionnaires', ''),
        ]


class TrialCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Trial
    form_class = forms.TrialForm

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['study'] = self.study
        return kwargs

    def _trial_by_id(self, id):
        if id:
            try:
                return models.Trial.objects.get(id=id)
            except models.Trial.DoesNotExist:
                pass
        return None

    def form_valid(self, form):
        active_trial = self._trial_by_id(form.instance.id)
        if active_trial:
            return redirect('rating-intro', self.study.slug, active_trial.slug)
        form.instance.study = self.study
        form.instance.init(self.study)
        response = super().form_valid(form)
        form.instance.generate_id()
        form.instance.generate_items()
        return response

    def get_success_url(self):
        return reverse('rating-intro', args=[self.study.slug, self.object.slug])


class TrialListView(LoginRequiredMixin, generic.ListView):
    model = models.Trial
    title = 'Trials'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def show_counter(self):
        return not self.study.allow_anonymous

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study-run', args=[self.study.slug])),
            ('trials', ''),
        ]


class TrialDetailView(LoginRequiredMixin, generic.DetailView):
    model = models.Trial
    title = 'Trial Overview'

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study-run', args=[self.study.slug])),
            ('trials', reverse('trials', args=[self.study.slug])),
            (self.object.id, ''),
        ]


class TrialDeleteView(LoginRequiredMixin, contrib_views.DefaultDeleteView):
    model = models.Trial

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

    def get_success_url(self):
        return reverse('trials', args=[self.study.slug])


class RatingIntroView(generic.TemplateView):
    template_name = 'lrex_trial/rating_intro.html'

    def _redirect_started(self):
        try:
            if self.trial.status == models.TrialStatus.FINISHED:
                return reverse('rating-taken', args=[self.study.slug, self.trial.slug])
            n_ratings = len(models.Rating.objects.filter(trial_item__trial=self.trial))
            return reverse('rating-create', args=[self.study.slug, self.trial.slug, n_ratings])
        except models.Rating.DoesNotExist:
            pass
        except models.TrialItem.DoesNotExist:
            pass
        return None

    def dispatch(self, *args, **kwargs):
        trial_slug = self.kwargs['slug']
        self.trial = models.Trial.objects.get(slug=trial_slug)
        self.study = self.trial.questionnaire.study
        redirect_link = self._redirect_started()
        if redirect_link:
            return redirect(redirect_link)
        return super().dispatch(*args, **kwargs)


class RatingOutroView(generic.TemplateView):
    template_name = 'lrex_trial/rating_outro.html'

    def dispatch(self, *args, **kwargs):
        trial_slug = self.kwargs['slug']
        self.trial = models.Trial.objects.get(slug=trial_slug)
        self.study = self.trial.questionnaire.study
        return super().dispatch(*args, **kwargs)


class RatingTakenView(generic.TemplateView):
    template_name = 'lrex_trial/rating_taken.html'


class RatingCreateView(generic.CreateView):
    model = models.Rating
    form_class = forms.RatingForm

    def dispatch(self, *args, **kwargs):
        trial_slug = self.kwargs['slug']
        self.num = int(self.kwargs['num'])
        self.trial = models.Trial.objects.get(slug=trial_slug)
        if self.trial.status == models.TrialStatus.FINISHED:
            return redirect(reverse('rating-taken', args=[self.study.slug, self.trial.slug]))
        self.study = self.trial.questionnaire.study
        self.trial_item = models.TrialItem.objects.get(
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
            return reverse('rating-create', args=[self.study.slug, self.trial.slug, self.num + 1])
        return reverse('rating-outro', args=[self.study.slug, self.trial.slug])
