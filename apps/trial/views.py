from markdownx.utils import markdownify

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.urls import reverse
from django.utils.functional import cached_property
from django.views import generic

from apps.contrib import csv as contrib_csv
from apps.contrib import views as contrib_views
from apps.experiment import views as experiment_views
from apps.study import views as study_views

from . import forms
from . import models


class QuestionnaireMixin:
    questionnaire_object = None
    slug_url_kwarg = 'questionnaire_slug'

    @property
    def study(self):
        return self.questionnaire.study

    @property
    def questionnaire(self):
        if not self.questionnaire_object:
            questionnaire_slug = self.kwargs['questionnaire_slug']
            self.questionnaire_object = models.Questionnaire.objects.get(slug=questionnaire_slug)
        return self.questionnaire_object


class QuestionnaireObjectMixin(QuestionnaireMixin):

    @property
    def questionnaire(self):
        if not self.questionnaire_object:
            self.questionnaire_object =  self.get_object()
        return self.questionnaire_object


    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['study'] = self.study
        data['questionnaire'] = self.questionnaire
        return data


class TrialMixin:
    trial_object = None
    slug_url_kwarg = 'trial_slug'

    @property
    def study(self):
        return self.trial.questionnaire.study

    @property
    def trial(self):
        if not self.trial_object:
            trial_slug = self.kwargs['trial_slug']
            self.trial_object = models.Trial.objects.get(slug=trial_slug)
        return self.trial_object

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['study'] = self.study
        data['trial'] = self.trial
        return data


class TrialObjectMixin(TrialMixin):

    @property
    def trial(self):
        if not self.trial_object:
            self.trial_object =  self.get_object()
        return self.trial_object


class QuestionnaireListView(study_views.StudyMixin, study_views.CheckStudyCreatorMixin, study_views.NextStepsMixin,
                            study_views.DisableFormIfStudyActiveMixin, generic.ListView):
    model = models.Questionnaire
    title = 'Questionnaires'
    page = 1
    paginate_by = 16

    def get(self, request, *args, **kwargs):
        if not self.study.is_allowed_pseudo_randomization:
            messages.info(request, 'Note: Define filler experiments to use pseudo randomization.')
        return super().get(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.page = request.GET.get('page', 1)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['allow_actions'] = self.study.is_allowed_create_questionnaires
        return data

    def _create_default_questionnaire_block(self, randomization):
        models.QuestionnaireBlock.objects.filter(study=self.study).delete()
        models.QuestionnaireBlock.objects.create(
            study=self.study,
            block=1,
            randomization=randomization,
        )

    def _get_randomization(self, action):
        if action == 'generate_random':
            return models.QuestionnaireBlock.RANDOMIZATION_TRUE
        if action == 'generate_ordered':
            return models.QuestionnaireBlock.RANDOMIZATION_NONE
        if action == 'generate_pseudo':
            return models.QuestionnaireBlock.RANDOMIZATION_PSEUDO

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if self.study.use_blocks:
            return redirect('questionnaire-generate',study_slug=self.study.slug)
        randomization = self._get_randomization(action)
        self._create_default_questionnaire_block(randomization)
        try:
            self.study.generate_questionnaires()
            messages.success(request, 'Questionnaires generated')
        except RuntimeError:
            messages.error(request, 'Pseudo-randomization timed out. Retry or add more filler items.')
        return redirect('questionnaires',study_slug=self.study.slug)

    def get_queryset(self):
        return super().get_queryset().filter(study=self.study)

    @property
    def pagination_offset(self):
        return (int(self.page) - 1) * int(self.paginate_by)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('questionnaires', ''),
        ]


class QuestionnaireDetailView(QuestionnaireObjectMixin, study_views.CheckStudyCreatorMixin, study_views.NextStepsMixin,
                              generic.DetailView):
    model = models.Questionnaire
    title = 'Questionnaire'

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('questionnaires', reverse('questionnaires', args=[self.study.slug])),
            (self.questionnaire.number, '')
        ]


class QuestionnaireGenerateView(study_views.StudyMixin, study_views.CheckStudyCreatorMixin,
                                study_views.DisableFormIfStudyActiveMixin, generic.TemplateView):
    title = 'Generate questionnaires'
    template_name = 'lrex_contrib/crispy_formset_form.html'
    formset = None
    helper = None

    def dispatch(self, request, *args, **kwargs):
        self.helper = forms.questionnaire_block_formset_helper()
        self.blocks = self.study.item_blocks
        if not self.study.is_allowed_pseudo_randomization:
            messages.info(request, 'Note: Define filler experiments to use pseudo randomization.')
        return super().dispatch(request, *args, **kwargs)

    def _initialize_questionnaire_blocks(self):
        existing_blocks = models.QuestionnaireBlock.objects.filter(study=self.study)
        if len(existing_blocks) != len(self.blocks):
            for block in existing_blocks: block.delete()
            for block in self.blocks:
                models.QuestionnaireBlock.objects.create(
                    study=self.study,
                    block=block,
                )

    def get(self, request, *args, **kwargs):
        self._initialize_questionnaire_blocks()
        self.formset = forms.questionnaire_block_factory(len(self.blocks))(
            queryset=models.QuestionnaireBlock.objects.filter(study=self.study)
        )
        forms.customize_randomization(self.formset, self.study)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'submit' in request.POST:
            self.formset = forms.questionnaire_block_factory(len(self.blocks))(request.POST, request.FILES)
            forms.customize_randomization(self.formset, self.study)
            if self.formset.is_valid():
                self.formset.save(commit=True)
                try:
                    self.study.generate_questionnaires()
                    messages.success(request, 'Questionnaires generated')
                except RuntimeError:
                    messages.error(request, 'Pseudo-randomization timed out. Retry or add more filler items and retry.')
                return redirect('questionnaires', study_slug=self.study.slug)
        return super().get(request, *args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('questionnaires', reverse('questionnaires', args=[self.study.slug])),
            ('generate', '')
        ]


class QuestionnaireDeleteAllView(study_views.StudyMixin, study_views.CheckStudyCreatorMixin,
                              study_views.DisableFormIfStudyActiveMixin, generic.TemplateView):
    title = 'Confirm Delete'
    template_name = 'lrex_contrib/confirm_delete.html'
    message = 'Delete all questionnaires?'

    def post(self, request, *args, **kwargs):
        self.study.delete_questionnaires()
        messages.success(self.request, 'All quetionnaires deleted')
        return redirect(self.get_success_url())

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('questionnaires', reverse('questionnaires', args=[self.study.slug])),
            ('delete', '')
        ]

    def get_success_url(self):
        return reverse('questionnaires', args=[self.study.slug])




class QuestionnaireBlockInstructionsUpdateView(study_views.StudyMixin, study_views.CheckStudyCreatorMixin, generic.TemplateView):
    title = 'Edit questionnaire block instructions'
    template_name = 'lrex_contrib/crispy_formset_form.html'
    formset = None
    helper = None

    def dispatch(self, *args, **kwargs):
        self.helper = forms.questionnaire_block_update_formset_helper()
        self.blocks = self.study.item_blocks
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.formset = forms.questionnaire_block_update_factory(len(self.blocks))(
            queryset=models.QuestionnaireBlock.objects.filter(study=self.study)
        )
        disable_form = False
        if self.study.use_blocks and not self.study.has_questionnaires:
            disable_form = True
        if not self.study.use_blocks:
            disable_form = True
            messages.info(request, 'Blocks are disabled for this study.')
        if disable_form:
            for helper_input in self.helper.inputs:
                helper_input.field_classes += '  disabled'
                helper_input.flat_attrs += '  disabled=True'
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'submit' in request.POST:
            self.formset = forms.questionnaire_block_update_factory(len(self.blocks))(request.POST, request.FILES)
            if self.formset.is_valid():
                self.formset.save(commit=True)
                messages.success(request, 'Block instructions updated')
                return redirect('study', study_slug=self.study.slug)
        return super().get(request, *args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('block-instructions', '')
        ]


class QuestionnaireUploadView(study_views.StudyMixin, study_views.CheckStudyCreatorMixin,
                              study_views.DisableFormIfStudyActiveMixin, generic.FormView,):
    title = 'Upload custom questionnaires'
    form_class = forms.UploadQuestionnaireForm
    template_name = 'lrex_contrib/crispy_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['study'] = self.study
        return kwargs

    def form_valid(self, form):
        result =  super().form_valid(form)
        self.study.questionnaire_set.all().delete()
        columns = {
            'questionnaires': form.cleaned_data['questionnaires_column'] - 1,
            'items': form.cleaned_data['items_column'] - 1,
            'lists': form.cleaned_data['item_lists_column'] - 1,
        }
        data = contrib_csv.read_file(form.cleaned_data)
        self.study.questionnaires_csv_restore(data, user_columns=columns, detected_csv=form.detected_csv)
        messages.success(self.request, 'Questionnaires uploaded')
        return result

    def get_success_url(self):
        return reverse('questionnaires', args=[self.study.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('questionnaires', reverse('questionnaires', args=[self.study.slug])),
            ('upload', '')
        ]


class QuestionnaireCSVDownloadView(study_views.StudyMixin, study_views.CheckStudyCreatorMixin, generic.View):

    def get(self, request, *args, **kwargs):
        filename = '{}_QUESTIONNAIRES_{}.csv'.format(self.study.title.replace(' ', '_'), str(now().date()))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        self.study.questionnaires_csv(response)
        return response


class TrialListView(study_views.StudyMixin, study_views.CheckStudyCreatorMixin, generic.ListView):
    model = models.Trial
    title = 'Trials'
    paginate_by = 16

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'download_proofs':
            filename = '{}_PROOFS_{}.csv'.format(self.study.title.replace(' ', '_'), str(now().date()))
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
            self.study.rating_proofs_csv(response)
            return response
        return redirect('trials', study_slug=self.study.slug)

    def get_queryset(self):
        return super().get_queryset().filter(questionnaire__study=self.study)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('trials', ''),
        ]


class TrialDeleteAllView(study_views.StudyMixin, study_views.CheckStudyCreatorMixin, generic.TemplateView):
    title = 'Confirm Delete'
    template_name = 'lrex_contrib/confirm_delete.html'
    message = 'Delete all trials?'

    def post(self, request, *args, **kwargs):
        models.Trial.objects.filter(questionnaire__study=self.study).delete()
        messages.success(self.request, 'All trials deleted')
        return redirect(self.get_success_url())

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('trials', reverse('trials', args=[self.study.slug])),
            ('delete-all', ''),
        ]

    def get_success_url(self):
        return reverse('study', args=[self.study.slug])


class TrialCreateView(study_views.StudyMixin, generic.CreateView):
    model = models.Trial
    form_class = forms.TrialForm

    @cached_property
    def is_test_trial(self):
        return bool(self.request.GET.get('test', False))

    def get(self, request, *args, **kwargs):
        if self.is_test_trial:
            messages.warning(request, 'Warning: This is a test trial.')
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['study'] = self.study
        kwargs['is_test'] = self.is_test_trial
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['instructions_rich'] = mark_safe(markdownify(self.study.instructions))
        data['is_test'] = self.is_test_trial
        return data

    def _trial_by_id(self, id):
        if id:
            try:
                return models.Trial.objects.get(questionnaire__study=self.study, subject_id=id)
            except models.Trial.DoesNotExist:
                pass
        return None

    def form_valid(self, form):
        active_trial = self._trial_by_id(form.instance.subject_id)
        if active_trial:
            active_trial_url = reverse('rating-create', args=[active_trial.slug, 0])
            return redirect(active_trial_url)
        if self.is_test_trial:
            if not form.instance.subject_id:
                form.instance.subject_id = 'Test'
            form.instance.is_test = True
        form.instance.init(self.study)
        return super().form_valid(form)

    def get_success_url(self):
        if self.study.use_blocks:
            return reverse('rating-block-instructions', args=[self.object.slug, 0])
        return reverse('rating-create', args=[self.object.slug, 0])


class TrialDetailView(TrialObjectMixin, study_views.CheckStudyCreatorMixin, generic.DetailView):
    model = models.Trial
    title = 'Trial overview'

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('trials', reverse('trials', args=[self.study.slug])),
            (self.trial.subject_id, ''),
        ]


class TrialDeleteView(TrialObjectMixin, study_views.CheckStudyCreatorMixin, contrib_views.DefaultDeleteView):
    model = models.Trial

    def delete(self, *args, **kwargs):
        results = super().delete(*args, **kwargs)
        for experiment in self.study.experiments:
            experiment_views.ExperimentResultsView.clear_cache(experiment)
        return results

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.object.slug, reverse('study', args=[self.object.slug])),
            ('delete', ''),
        ]

    def get_success_url(self):
        return reverse('trials', args=[self.study.slug])


class ProgressMixin:

    def get_context_data(self, **kwargs):
        num = kwargs['num']
        count = kwargs['n_trial_items']
        data = super().get_context_data(**kwargs)
        i = num + 1
        data['progress_i'] =  i
        data['progress_count'] = count
        data['progress'] = i * 100 / (count + 1)
        return data


class TestWarningMixin:

    def get(self, request, *args, **kwargs):
        if self.trial.is_test:
            messages.warning(request, 'Warning: This is a test trial.')
        return super().get(request, *args, **kwargs)


class RatingCreateMixin(ProgressMixin, TestWarningMixin):

    def get_context_data(self, **kwargs):
        kwargs.update(
            {'n_trial_items': len(self.trial.items), 'num': self.num}
        )
        return super().get_context_data(**kwargs)
        return super().get_context_data(**kwargs)

    def _redirect_to_correct_num(self, num):
        try:
            if self.trial.status == models.TrialStatus.FINISHED:
                return reverse('rating-taken', args=[self.trial.slug])
            n_ratings = models.Rating.objects.filter(trial=self.trial, question=0).count()
            if n_ratings != num:
                return reverse('rating-create', args=[self.trial.slug, n_ratings])
        except models.Rating.DoesNotExist:
            pass
        return None

    def get_next_url(self):
        trial_items = self.trial.items
        if self.num < len(trial_items) - 1:
            if self.study.use_blocks and trial_items[self.num].block != trial_items[self.num + 1].block:
                return reverse('rating-block-instructions', args=[self.trial.slug, self.num + 1])
            return reverse('rating-create', args=[self.trial.slug, self.num + 1])
        return reverse('rating-outro', args=[self.trial.slug])


class RatingCreateView(RatingCreateMixin, TrialMixin, generic.CreateView):
    model = models.Rating
    form_class = forms.RatingForm

    def dispatch(self, *args, **kwargs):
        self.num = int(self.kwargs['num'])
        redirect_link = self._redirect_to_correct_num(self.num)
        if not redirect_link and self.study.is_multi_question:
            redirect_link = reverse('ratings-create', args=[self.trial.slug, self.num])
        if redirect_link:
            return redirect(redirect_link)
        self.questionnaire_item = models.QuestionnaireItem.objects.get(
            questionnaire=self.trial.questionnaire,
            number=self.num
        )
        self.item_questions = self.questionnaire_item.item.itemquestion_set.all()
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.questionnaire_item.rating_set.filter(trial=self.trial).exists():
            return redirect(self.get_next_url())
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['study'] = self.study
        kwargs['question'] = self.study.question
        if self.item_questions:
            kwargs['item_question'] = self.item_questions[0]
        return kwargs

    def form_valid(self, form):
        form.instance.trial = self.trial
        form.instance.questionnaire_item = self.questionnaire_item
        for experiment in self.study.experiments:
            experiment_views.ExperimentResultsView.clear_cache(experiment)
        return super().form_valid(form)

    def get_success_url(self):
        return self.get_next_url()


class RatingsCreateView(RatingCreateMixin, TrialMixin, generic.TemplateView):
    model = models.Rating
    template_name = 'lrex_trial/ratings_form.html'

    formset = None
    helper = None

    def dispatch(self, request, *args, **kwargs):
        self.num = int(self.kwargs['num'])
        redirect_link = self._redirect_to_correct_num(self.num)
        if redirect_link:
            return redirect(redirect_link)
        self.questionnaire_item = models.QuestionnaireItem.objects.get(
            questionnaire=self.trial.questionnaire,
            number=self.num
        )
        self.n_questions = len(self.study.questions)
        self.item_questions = self.questionnaire_item.item.itemquestion_set.all()
        self.helper = forms.rating_formset_helper(self.study.continue_label)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.formset = forms.ratingformset_factory(self.n_questions)(
            queryset=models.Rating.objects.none()
        )
        forms.customize_to_questions(
            self.formset, self.study.questions, self.item_questions, self.questionnaire_item, self.study.pseudo_randomize_question_order
        )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.questionnaire_item.rating_set.filter(trial=self.trial).exists():
            return redirect(self.get_next_url())
        self.formset = forms.ratingformset_factory(self.n_questions)(request.POST, request.FILES)
        forms.customize_to_questions(
            self.formset, self.study.questions, self.item_questions, self.questionnaire_item, self.study.pseudo_randomize_question_order
        )
        if self.formset.is_valid():
            instances = self.formset.save(commit=False)
            if len(instances) < self.n_questions:
                self.formset._non_form_errors = \
                    self.formset.error_class(ValidationError('Please answer all questions').error_list)
            else:
                for instance in instances:
                    instance.trial = self.trial
                    instance.questionnaire_item = self.questionnaire_item
                    instance.save()
                for experiment in self.study.experiments:
                    experiment_views.ExperimentResultsView.clear_cache(experiment)
                return redirect(self.get_next_url())
        return super().get(request, *args, **kwargs)


class RatingBlockInstructionsView(ProgressMixin, TestWarningMixin, TrialMixin, generic.TemplateView):
    template_name = 'lrex_trial/rating_block_instructions.html'

    def get_context_data(self, **kwargs):
        kwargs.update(
            {'n_trial_items': len(self.trial.items)}
        )
        num = self.kwargs['num']
        data = super().get_context_data(**kwargs)
        questionnaire_item = models.QuestionnaireItem.objects.get(
            questionnaire=self.trial.questionnaire,
            number=num
        )
        questionnaire_block = models.QuestionnaireBlock.objects.get(
            study=self.study,
            block=questionnaire_item.item.block
        )
        data['block_instructions_rich'] = mark_safe(markdownify(questionnaire_block.instructions))
        data['trial'] = self.trial
        return data


class RatingOutroView(TrialMixin, TestWarningMixin, generic.TemplateView):
    template_name = 'lrex_trial/rating_outro.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.study.generate_participation_code:
            data['generated_rating_proof'] = self.trial.generate_rating_proof()
        data['outro_rich'] = mark_safe(markdownify(self.study.outro))
        return data


class RatingTakenView(TrialMixin, TestWarningMixin, generic.TemplateView):
    template_name = 'lrex_trial/rating_taken.html'


