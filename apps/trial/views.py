from itertools import groupby
from markdownx.utils import markdownify

from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator
from django.db.utils import IntegrityError
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.urls import reverse
from django.utils.functional import cached_property
from django.views import generic

from apps.contrib import csv as contrib_csv
from apps.contrib import views as contrib_views
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

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['study'] = self.study
        data['questionnaire'] = self.questionnaire
        return data


class QuestionnaireObjectMixin(QuestionnaireMixin):

    @property
    def questionnaire(self):
        if not self.questionnaire_object:
            self.questionnaire_object =  self.get_object()
        return self.questionnaire_object


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
        context = super().get_context_data(**kwargs)
        context.update({
            'study': self.study,
            'trial': self.trial,
        })
        return context


class TrialObjectMixin(TrialMixin):

    @property
    def trial(self):
        if not self.trial_object:
            self.trial_object =  self.get_object()
        return self.trial_object


class QuestionnaireListView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    study_views.QuestionnaireNavMixin,
    generic.ListView
):
    model = models.Questionnaire
    title = 'Questionnaires'
    page = 1
    paginate_by = 16

    randomization_form = None

    def _get_prev_randomization(self):
        block = models.QuestionnaireBlock.objects.filter(study=self.study).first()
        return block.randomization if block else None

    def get(self, request, *args, **kwargs):
        if not self.study.is_allowed_pseudo_randomization:
            messages.info(request, 'Note: Define filler materials to use pseudo randomization.')
        if not self.study.use_blocks:
            randomization = self._get_prev_randomization()
            self.randomization_form = forms.RandomizationForm(
                randomization=randomization,
                allow_pseudo_random=self.study.is_allowed_pseudo_randomization
            )
            if self.is_disabled:
                self.disable_form(self.randomization_form)
        return super().get(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.page = request.GET.get('page', 1)
        return super().dispatch(request, *args, **kwargs)

    @property
    def is_disabled(self):
        return self.study.is_active or not self.study.is_allowed_create_questionnaires

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if not self.study.use_blocks:
            data['generate_form'] = self.randomization_form
        return data

    def _update_default_questionnaire_block(self, randomization):
        block = models.QuestionnaireBlock.objects.filter(study=self.study).first()
        if block:
            block.randomization = randomization
            block.save()
        else:
            models.QuestionnaireBlock.objects.create(study=self.study, block=1, randomization=randomization)

    def post(self, request, *args, **kwargs):
        if self.study.use_blocks:
            return redirect('questionnaire-generate',study_slug=self.study.slug)
        self.randomization_form = forms.RandomizationForm(
            request.POST, request.FILES,
            allow_pseudo_random=self.study.is_allowed_pseudo_randomization
        )
        if self.randomization_form.is_valid():
            randomization = self.randomization_form['randomization'].value()
            self._update_default_questionnaire_block(randomization)
            try:
                self.study.generate_questionnaires()
                messages.success(request, 'Questionnaires generated.')
            except RuntimeError:
                messages.error(request, 'Pseudo-randomization timed out. Retry or add more filler items and retry.')
        return redirect('questionnaires',study_slug=self.study.slug)

    def get_queryset(self):
        return super().get_queryset().filter(study=self.study)


    @property
    def pagination_offset(self):
        return (int(self.page) - 1) * int(self.paginate_by)


class QuestionnaireDetailView(
    QuestionnaireObjectMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.QuestionnaireNavMixin,
    generic.DetailView
):
    model = models.Questionnaire

    @cached_property
    def title(self):
        return 'Questionnaire {}'.format(self.questionnaire.number)

    def _items_for_block(self, block, q_items):
        return [(block, q_item, q_item.question_properties.all()) for q_item in q_items]

    def _context_questionnaire_items(self):
        context_items = []
        if self.study.use_blocks:
            questionnaire_items = self.questionnaire.questionnaire_items.prefetch_related('question_properties').all()
            for block, q_items in groupby(questionnaire_items, lambda q_item: q_item.item.materials_block):
                context_items.extend(self._items_for_block(block, q_items))
        else:
            context_items.extend(self._items_for_block(1, self.questionnaire.questionnaire_items.all()))
        return context_items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questionnaire_items'] = self._context_questionnaire_items()
        return context


class QuestionnaireGenerateView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    study_views.QuestionnaireNavMixin,
    contrib_views.FormsetView,
):
    title = 'Generate questionnaires'
    template_name = 'lrex_dashboard/questionnaire_formset_form.html'
    formset_factory = forms.QuestionnaireGenerateFormsetFactory

    item_blocks = None

    def get_formset_queryset(self):
        return self.study.questionnaire_blocks.all()

    def get_form_count(self):
        return len(self.item_blocks)

    def save_form(self, form, number):
        form.instance.block = number + 1
        form.instance.study = self.study
        super().save_form(form, number)

    def submit_redirect(self):
        return redirect('questionnaires', study_slug=self.study.slug)

    def dispatch(self, request, *args, **kwargs):
        self.item_blocks = self.study.item_blocks
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if not self.study.is_allowed_pseudo_randomization:
            messages.info(request, 'Note: Define filler materials to use pseudo randomization.')
        return super().get(request, *args, **kwargs)

    def _initialize_questionnaire_blocks(self):
        existing_blocks = models.QuestionnaireBlock.objects.filter(study=self.study)
        if len(existing_blocks) != len(self.item_blocks):
            for block in existing_blocks:
                block.delete()
            for block in self.item_blocks:
                models.QuestionnaireBlock.objects.create(
                    study=self.study,
                    block=block,
                )

    def formset_valid(self):
        self._initialize_questionnaire_blocks()
        try:
            self.study.generate_questionnaires()
            messages.success(self.request, 'Questionnaires generated.')
        except RuntimeError:
            messages.error(self.request, 'Pseudo-randomization timed out. Retry or add more filler items and retry.')


class QuestionnaireDeleteAllView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    study_views.QuestionnaireNavMixin,
    generic.TemplateView
):
    title = 'Confirm deletion'
    template_name = 'lrex_dashboard/questionnaire_confirm_delete.html'
    message = 'Delete all questionnaires?'

    def post(self, request, *args, **kwargs):
        self.study.delete_questionnaires()
        self.study.delete_questionnaire_blocks()
        messages.success(self.request, 'All questionnaires deleted.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('questionnaires', args=[self.study.slug])


class QuestionnaireBlockInstructionsUpdateView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    contrib_views.LeaveWarningMixin,
    contrib_views.DisableFormMixin,
    study_views.QuestionnaireNavMixin,
    contrib_views.FormsetView,
):
    title = 'Edit questionnaire block instructions'
    template_name = 'lrex_dashboard/questionnaire_formset_form.html'
    formset_factory = forms.QuestionnaireBlockFormsetFactory

    def get_formset_queryset(self):
        return self.study.questionnaire_blocks.all()

    def get_form_count(self):
        return self.study.questionnaire_blocks.count()

    def submit_redirect(self):
        return redirect('questionnaires', study_slug=self.study.slug)

    def get(self, request, *args, **kwargs):
        if not self.study.use_blocks:
            messages.info(request, 'Blocks are disabled for this study.')
        if not self.study.items_validated:
            messages.info(request, 'All materials items need to be validated before creating block instructions.')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'nav2_active': 1,
        })
        return context

    @property
    def is_disabled(self):
        if self.study.is_active or not self.study.use_blocks:
            return True
        if not self.study.items_validated:
            return True
        return False



class QuestionnaireUploadView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    study_views.QuestionnaireNavMixin,
    generic.FormView,
):
    title = 'Upload custom questionnaires'
    form_class = forms.QuestionnaireUploadForm
    template_name = 'lrex_dashboard/questionnaire_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['study'] = self.study
        return kwargs

    def form_valid(self, form):
        result =  super().form_valid(form)
        self.study.questionnaires.all().delete()
        columns = {
            'questionnaires': form.cleaned_data['questionnaires_column'] - 1,
            'items': form.cleaned_data['items_column'] - 1,
            'lists': form.cleaned_data['item_lists_column'] - 1,
        }
        data = contrib_csv.read_file(form.cleaned_data)
        self.study.questionnaires_from_csv(data, user_columns=columns, detected_csv=form.detected_csv)
        messages.success(self.request, 'Questionnaires uploaded.')
        return result

    def get_success_url(self):
        return reverse('questionnaires', args=[self.study.slug])


class QuestionnaireCSVDownloadView(study_views.StudyMixin, study_views.CheckStudyCreatorMixin, generic.View):

    def get(self, request, *args, **kwargs):
        filename = '{}_QUESTIONNAIRES_{}.csv'.format(self.study.title.replace(' ', '_'), str(now().date()))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        self.study.questionnaires_csv(response)
        return response


class TrialListView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.ResultsNavMixin,
    generic.ListView
):
    model = models.Trial
    title = 'Trials'
    paginate_by = 16

    def get(self, request, *args, **kwargs):
        if self.study.has_participant_information:
            message = (
                'Please remove the participant information when not needed anymore to reduce the stored personal data.'
            )
            messages.warning(request, message)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action:
            if action == 'delete_tests':
                self.study.delete_test_trials()
                messages.success(request, 'All test trials deleted.')
            elif action == 'delete_abandoned':
                self.study.delete_abandoned_trials()
                messages.success(request, 'All abandoned trials deleted.')
        return redirect('trials', study_slug=self.study.slug)

    def get_queryset(self):
        return super().get_queryset().filter(questionnaire__study=self.study)


class TrialParticipantsCSVDownloadView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    generic.View,
):

    def get(self, request, *args, **kwargs):
        filename = '{}_PARTICIPANTS_{}.csv'.format(self.study.title.replace(' ', '_'), now().strftime('%Y-%m-%d-%H%M'))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        self.study.participant_information_csv(response)
        return response


class TrialDeleteParticipantsView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.ResultsNavMixin,
    generic.TemplateView,
):
    title = 'Confirm deletion'
    template_name = 'lrex_dashboard/results_confirm_delete.html'
    message = 'Delete participant information? This includes participant IDs, demographic data and participation times.'

    def get_success_url(self):
        return reverse('trials', args=[self.study.slug])

    def post(self, request, *args, **kwargs):
        self.study.delete_participant_information()
        messages.success(request, 'Participant information deleted.')
        return redirect(self.get_success_url())


class TrialDeleteAllView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.ResultsNavMixin,
    generic.TemplateView,
):
    title = 'Confirm deletion'
    template_name = 'lrex_dashboard/results_confirm_delete.html'
    message = 'Delete all trials?'

    def get_success_url(self):
        return reverse('trials', args=[self.study.slug])

    def post(self, request, *args, **kwargs):
        models.Trial.objects.filter(questionnaire__study=self.study).delete()
        messages.success(self.request, 'All trials deleted.')
        return redirect(self.get_success_url())


class TestTrialMixin:
    message = 'Note: This is a test trial.'

    @cached_property
    def is_test_trial(self):
        return bool(self.request.GET.get('test', False))

    def get(self, request, *args, **kwargs):
        if self.is_test_trial:
            messages.warning(request, self.message)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.is_test_trial:
            messages.warning(request, self.message)
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['study'] = self.study
        kwargs['is_test'] = self.is_test_trial
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['is_test'] = self.is_test_trial
        return data

    def test_url(self, url):
        if self.is_test_trial:
            url += '?test=True'
        return url


class TrialIntroView(study_views.StudyMixin, TestTrialMixin, generic.FormView):
    form_class = forms.ConsentForm
    template_name = 'lrex_trial/trial_intro.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['study'] = self.study
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'intro_rich': mark_safe(markdownify(self.study.intro)),
            'consent_form_text_rich': mark_safe(markdownify(self.study.consent_form_text)),
            'contact': mark_safe(self.study.contact),
            'contact_details_rich': mark_safe(markdownify(self.study.contact_details)) if self.study.contact_details else None,
        })
        return context

    def get_success_url(self):
        return self.test_url(reverse('trial-create', args=[self.study.slug]))


class TrialCreateView(study_views.StudyMixin, TestTrialMixin, generic.CreateView):
    model = models.Trial
    form_class = forms.TrialForm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['instructions_rich'] = mark_safe(markdownify(self.study.instructions))
        return data

    def _trial_by_id(self, id):
        if id:
            try:
                return models.Trial.objects.get(questionnaire__study=self.study, participant_id=id)
            except models.Trial.DoesNotExist:
                pass
        return None

    def form_valid(self, form):
        active_trial = self._trial_by_id(form.instance.participant_id)
        if active_trial:
            active_trial_url = reverse('ratings-create', args=[active_trial.slug, 0])
            return redirect(active_trial_url)
        if self.is_test_trial:
            if not form.instance.participant_id:
                form.instance.participant_id = 'Test'
            form.instance.is_test = True
        form.instance.init(self.study)
        return super().form_valid(form)

    def get_success_url(self):
        if self.study.has_demographics:
            url = reverse('trial-demographics', args=[self.object.slug])
        elif self.study.use_blocks:
            url = reverse('rating-block-instructions', args=[self.object.slug, 0])
        else:
            url = reverse('ratings-create', args=[self.object.slug, 0])
        url = self.test_url(url)
        return url


class DemographicsCreateView(TrialMixin, TestTrialMixin, contrib_views.FormsetView):
    model = models.Rating
    template_name = 'lrex_trial/trial_demographics.html'
    formset_factory = forms.DemographicsValueFormsetFactory
    custom_formset = forms.DemographicsValueFormset

    def get_formset_queryset(self):
        return self.trial.demographics.all()

    def get_form_count(self):
        return self.study.demographics.count()

    def save_form(self, form, number):
        form.instance.field = self.study.demographics.get(number=number)
        form.instance.trial = self.trial
        super().save_form(form, number)

    def submit_redirect(self):
        if self.study.use_blocks:
            url = reverse('rating-block-instructions', args=[self.trial.slug, 0])
        else:
            url = reverse('ratings-create', args=[self.trial.slug, 0])
        url = self.test_url(url)
        return redirect(url)


class TrialDetailView(
    TrialObjectMixin,
    study_views.CheckStudyCreatorMixin,
    generic.DetailView,
):
    model = models.Trial
    title = 'Trial overview'
    paginate_by = 16

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trial = self.get_object()
        questionnaire_items = trial.questionnaire.questionnaire_items.all()
        questionnaire_items = questionnaire_items.prefetch_related(
            'ratings',
            'item',
            'item__materials',
        )
        if self.study.has_text_items:
            questionnaire_items = questionnaire_items.prefetch_related('item__textitem')
        elif self.study.has_markdown_items:
            questionnaire_items = questionnaire_items.prefetch_related('item__markdownitem')
        elif self.study.has_audiolink_items:
            questionnaire_items = questionnaire_items.prefetch_related('item__audiolinkitem')
        questionnaire_items_with_ratings = []
        for questionnaire_item in questionnaire_items.all():
            ratings = questionnaire_item.ratings.filter(trial=trial)
            questionnaire_items_with_ratings.append((questionnaire_item, ratings))
        paginator = Paginator(questionnaire_items_with_ratings, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context.update({
            'page_obj': page_obj,
        })
        return context


class TrialDeleteView(
    TrialObjectMixin,
    study_views.CheckStudyCreatorMixin,
    contrib_views.DefaultDeleteView,
):
    model = models.Trial
    template_name = 'lrex_dashboard/results_confirm_delete.html'

    def get_success_url(self):
        return reverse('trials', args=[self.study.slug])


class TrialHomeView(study_views.StudyMixin, generic.TemplateView):
    template_name = 'lrex_trial/trial_home.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['privacy_statement_rich'] = mark_safe(markdownify(settings.LREX_PRIVACY_MD))
        return data


class ProgressMixin:

    def get_context_data(self, **kwargs):
        num = kwargs['num']
        count = kwargs['n_trial_items']
        context = super().get_context_data(**kwargs)
        context.update({
            'progress_i': num,
            'progress_count': count,
            'progress': num * 100 / count,
        })
        return context


class RatingsCreateView(ProgressMixin, TestTrialMixin, TrialMixin, contrib_views.FormsetView):
    model = models.Rating
    template_name = 'lrex_trial/rating_form.html'
    formset_factory = forms.RatingFormsetFactory
    custom_formset = forms.RatingFormset

    HORIZONTAL_LAYOUT_LIMIT = 70

    def get_formset_queryset(self):
        return self.trial.rating_set.none()

    def get_form_count(self):
        return self.study.questions.count()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'questionnaire_item': self.questionnaire_item,
        })
        return kwargs

    def save_form(self, form, number):
        form.instance.trial = self.trial
        form.instance.questionnaire_item = self.questionnaire_item
        try:
            super().save_form(form, number)
        except IntegrityError:
            return redirect(self.get_next_url())

    def submit_redirect(self):
        if self.is_last:
            self.trial.ended = now()
            self.trial.save()
        return redirect(self.get_next_url())

    def formset_valid(self):
        pass

    def formset_invalid(self):
        if any('scale_value' in form_errors for form_errors in self.formset.errors):
            messages.error(self.request, self.study.answer_questions_message)
        if any('feedbacks_given' in form_errors for form_errors in self.formset.errors):
            messages.error(self.request, self.study.feedback_message)

    def dispatch(self, request, *args, **kwargs):
        self.num = int(self.kwargs['num'])
        redirect_link = self._redirect_to_correct_num(self.num)
        if redirect_link:
            return redirect(redirect_link)
        self.questionnaire_item = models.QuestionnaireItem.objects.prefetch_related(
            'item',
            'item__item_questions',
            'question_properties',
        ).get(
            questionnaire=self.trial.questionnaire,
            number=self.num
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs.update(
            {
                'continue_label': self.study.continue_label,
                'n_trial_items': len(self.trial.items), 'num': self.num,
                'item': self.questionnaire_item.item,
            }
        )
        context = super().get_context_data(**kwargs)
        context.update({
            'contact': mark_safe(self.study.contact),
            'use_vertical_scale_layout': self.study.use_vertical_scale_layout,
        })
        if self.study.short_instructions:
            context['short_instructions_rich'] = mark_safe(markdownify(self.study.short_instructions))
        if self.study.use_blocks and self.trial.current_block.short_instructions:
            context['short_block_instructions_rich'] = mark_safe(markdownify(self.trial.current_block.short_instructions))
        return context

    def _redirect_to_correct_num(self, num):
        if self.trial.is_test:
            return None
        if self.trial.is_finished:
            return reverse('rating-taken', args=[self.trial.slug])
        try:
            n_ratings = models.Rating.objects.filter(trial=self.trial, question=0).count()
            if n_ratings != num:
                return reverse('ratings-create', args=[self.trial.slug, n_ratings])
        except models.Rating.DoesNotExist:
            pass
        return None

    @cached_property
    def is_last(self):
        trial_items = self.trial.items
        return self.num == len(trial_items) - 1

    def get_next_url(self):
        if not self.is_last:
            trial_items = self.trial.items
            if (
                    self.study.use_blocks
                    and trial_items[self.num].materials_block != trial_items[self.num + 1].materials_block
            ):
                url = reverse('rating-block-instructions', args=[self.trial.slug, self.num + 1])
            else:
                url = reverse('ratings-create', args=[self.trial.slug, self.num + 1])
        else:
            url = reverse('rating-outro', args=[self.trial.slug])
        url = self.test_url(url)
        return url


class RatingBlockInstructionsView(ProgressMixin, TestTrialMixin, TrialMixin, generic.TemplateView):
    template_name = 'lrex_trial/rating_block_instructions.html'

    def get(self, request, *args, **kwargs):
        self.questionnaire_block = self.trial.current_block
        num = int(self.kwargs['num'])
        self.next_url = reverse('ratings-create', args=[self.trial.slug, num])
        self.next_url = self.test_url(self.next_url)
        if not self.questionnaire_block.instructions:
            return redirect(self.next_url)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs.update(
            {'n_trial_items': len(self.trial.items)}
        )
        context = super().get_context_data(**kwargs)
        context.update({
            'block_instructions_rich': mark_safe(markdownify(self.questionnaire_block.instructions)),
            'next_url': self.next_url,
        })
        return context


class RatingOutroView(TrialMixin, TestTrialMixin, generic.TemplateView):
    template_name = 'lrex_trial/rating_outro.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.study.participant_id == self.study.PARTICIPANT_ID_RANDOM:
            data['participant_id'] = self.trial.participant_id
        data['outro_rich'] = mark_safe(markdownify(self.study.outro))
        return data


class RatingTakenView(TrialMixin, TestTrialMixin, generic.TemplateView):
    template_name = 'lrex_trial/rating_taken.html'
