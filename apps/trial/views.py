from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse
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
        if action and action == 'generate_ordered':
            self.study.generate_questionnaires()
        elif action and action == 'generate_random':
            self.study.generate_questionnaires()
            self.study.randomize_questionnaires()
        self.study.set_progress(self.study.PROGRESS_STD_QUESTIONNARES_GENERATED)
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
                return models.Trial.objects.get(questionnaire__study=self.study, id=id)
            except models.Trial.DoesNotExist:
                pass
        return None

    def form_valid(self, form):
        active_trial = self._trial_by_id(form.instance.id)
        if active_trial:
            return reverse('rating-create', args=[self.study.slug, active_trial.slug, 0])
        form.instance.study = self.study
        form.instance.init(self.study)
        response = super().form_valid(form)
        form.instance.generate_id()
        form.instance.generate_items()
        return response

    def get_success_url(self):
        return reverse('rating-create', args=[self.study.slug, self.object.slug, 0])


class TrialListView(LoginRequiredMixin, generic.ListView):
    model = models.Trial
    title = 'Trials'
    paginate_by = 16

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['study_slug']
        self.study = study_models.Study.objects.get(slug=study_slug)
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'download_proofs':
            filename = self.study.slug + '-proofs.csv'
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
            self.study.rating_proofs_csv(response)
            return response
        return redirect('trials', study_slug=self.study.slug)

    def get_queryset(self):
        return super().get_queryset().filter(questionnaire__study=self.study)

    def show_counter(self):
        return self.study.require_participant_id

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study-run', args=[self.study.slug])),
            ('trials', ''),
        ]


class TrialDetailView(LoginRequiredMixin, generic.DetailView):
    model = models.Trial
    title = 'Trial overview'

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


class RatingOutroView(generic.TemplateView):
    template_name = 'lrex_trial/rating_outro.html'

    def dispatch(self, *args, **kwargs):
        trial_slug = self.kwargs['slug']
        self.trial = models.Trial.objects.get(slug=trial_slug)
        self.study = self.trial.questionnaire.study
        self.generated_rating_proof = self.trial.generate_rating_proof()
        return super().dispatch(*args, **kwargs)


class RatingTakenView(generic.TemplateView):
    template_name = 'lrex_trial/rating_taken.html'


class RatingCreateView(generic.CreateView):
    model = models.Rating
    form_class = forms.RatingForm

    def _redirect_active(self, num):
        try:
            if self.trial.status == models.TrialStatus.FINISHED:
                return reverse('rating-taken', args=[self.study.slug, self.trial.slug])
            n_ratings = models.Rating.objects.filter(trial_item__trial=self.trial).count()
            n_questions = self.study.question_set.count()
            if n_ratings/n_questions != num:
                return reverse('rating-create', args=[self.study.slug, self.trial.slug, n_ratings])
        except models.Rating.DoesNotExist:
            pass
        except models.TrialItem.DoesNotExist:
            pass
        return None

    def dispatch(self, *args, **kwargs):
        trial_slug = self.kwargs['slug']
        self.trial = models.Trial.objects.get(slug=trial_slug)
        self.num = int(self.kwargs['num'])
        self.study = self.trial.questionnaire.study
        redirect_link = self._redirect_active(self.num)
        if not redirect_link and self.study.question_set.count() > 1:
            redirect_link = reverse('ratings-create', args=[self.study.slug, self.trial.slug, self.num])
        if redirect_link:
            return redirect(redirect_link)
        self.trial_item = models.TrialItem.objects.get(
            trial__slug=trial_slug,
            number=self.num
        )
        self.question = self.study.question_set.first()
        self.item_questions = self.trial_item.item.itemquestion_set.all()
        return super().dispatch(*args, **kwargs)

    def progress(self):
        return self.num * 100 / len(self.trial.items)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['question'] = self.question
        if self.item_questions:
            kwargs['item_question'] = self.item_questions[0]
        return kwargs

    def form_valid(self, form):
        form.instance.number = self.num
        form.instance.trial_item = self.trial_item
        return super().form_valid(form)

    def get_success_url(self):
        if self.num < (len(self.trial.items) - 1):
            return reverse('rating-create', args=[self.study.slug, self.trial.slug, self.num + 1])
        return reverse('rating-outro', args=[self.study.slug, self.trial.slug])

    @property
    def item_question(self):
        if self.item_questions:
            return self.item_questions[0].question
        return self.question.question

    @property
    def item_legend(self):
        if self.item_questions:
            return self.item_questions[0].legend
        return self.question.legend



class RatingsCreateView(generic.TemplateView):
    model = models.Rating
    template_name = 'lrex_trial/ratings_form.html'

    formset = None
    helper = forms.rating_formset_helper

    def dispatch(self, *args, **kwargs):
        trial_slug = self.kwargs['slug']
        self.trial = models.Trial.objects.get(slug=trial_slug)
        self.num = int(self.kwargs['num'])
        self.study = self.trial.questionnaire.study
        self.trial_item = models.TrialItem.objects.get(
            trial__slug=trial_slug,
            number=self.num
        )
        self.questions = study_models.Question.objects.filter(
            study=self.study
        )
        self.item_questions = self.trial_item.item.itemquestion_set.all()
        self.formset = forms.ratingformset_factory(len(self.questions))(
            queryset=models.Rating.objects.none()
        )
        forms.customize_to_questions(self.formset, self.questions, self.item_questions)
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.formset = forms.ratingformset_factory(len(self.questions))(request.POST, request.FILES)
        forms.customize_to_questions(self.formset, self.questions, self.item_questions)
        if self.formset.is_valid():
            instances = self.formset.save(commit=False)
            if len(instances) < len(self.questions):
                self.formset._non_form_errors = \
                    self.formset.error_class(ValidationError('Please answer all questions').error_list)
            else:
                for instance in instances:
                    instance.trial_item = self.trial_item
                    instance.save()
                if self.num < (len(self.trial.items) - 1):
                    return redirect('rating-create', study_slug=self.study.slug, slug=self.trial.slug, num=self.num + 1)
                return redirect('rating-outro', study_slug=self.study.slug, slug=self.trial.slug)
        return super().get(request, *args, **kwargs)

    def progress(self):
        return self.num * 100 / len(self.trial.items)
