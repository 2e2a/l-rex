from markdownx.utils import markdownify

from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.urls import reverse
from django.utils.functional import cached_property
from django.views import generic

from apps.contrib import csv as contrib_csv
from apps.contrib import views as contrib_views
from apps.materials import views as materials_views
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


class QuestionnaireListView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.NextStepsMixin,
    study_views.DisableFormIfStudyActiveMixin,
    contrib_views.ActionsMixin,
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
            self.randomization_form = forms.RandomizationForm(randomization=randomization)
        return super().get(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.page = request.GET.get('page', 1)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['allow_actions'] = self.study.is_allowed_create_questionnaires
        if not self.study.use_blocks:
            data['generate_form'] = self.randomization_form
        return data

    def _update_default_questionnaire_block(self, randomization):
        block = models.QuestionnaireBlock.objects.filter(study=self.study).first()
        if block:
            block.randomization = randomization
            block.save()
        else:
            block = models.QuestionnaireBlock.objects.create(study=self.study, block=1, randomization=randomization)

    def post(self, request, *args, **kwargs):
        if self.study.use_blocks:
            return redirect('questionnaire-generate',study_slug=self.study.slug)
        self.randomization_form = forms.RandomizationForm(request.POST, request.FILES)
        if self.randomization_form.is_valid():
            randomization = self.randomization_form['randomization'].value()
            self._update_default_questionnaire_block(randomization)
            try:
                self.study.generate_questionnaires()
                messages.success(request, 'Questionnaires generated.')
            except RuntimeError:
                messages.error(request, 'Pseudo-randomization timed out. Retry or add more filler items.')
        return redirect('questionnaires',study_slug=self.study.slug)

    def get_queryset(self):
        return super().get_queryset().filter(study=self.study)

    @property
    def pagination_offset(self):
        return (int(self.page) - 1) * int(self.paginate_by)

    @property
    def actions(self):
        if self.study.use_blocks:
            return [(
                'link',
                'Generate questionnaires',
                reverse('questionnaire-generate', args=[self.study.slug]),
                self.ACTION_CSS_BUTTON_PRIMARY
            )]
        else:
            return [('form', self.randomization_form, self.randomization_form.helper)]


    @property
    def secondary_actions(self):
        return [
            ('link', 'Upload CSV', reverse('questionnaire-upload', args=[self.study.slug])),
            ('link', 'Download CSV', reverse('questionnaire-download', args=[self.study.slug])),
            ('link', 'Delete all', reverse('questionnaires-delete', args=[self.study.slug])),
        ]

    @property
    def disable_actions(self):
        if self.is_disabled:
            return [0, 1], [0, 2]

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('questionnaires', ''),
        ]


class QuestionnaireDetailView(
    QuestionnaireObjectMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.NextStepsMixin,
    generic.DetailView
):
    model = models.Questionnaire
    title = 'Questionnaire'

    def _add_items_for_block(self, context_items, block, q_items):
        for q_item in q_items:
            question_properties = q_item.question_properties
            context_items.append(
                (block, q_item, question_properties)
            )

    def _context_questionnaire_items(self):
        context_items = []
        if self.study.use_blocks:
            for block, q_items in self.questionnaire.questionnaire_items_by_block.items():
                self._add_items_for_block(context_items, block, q_items)
        else:
            self._add_items_for_block(context_items, 1, self.questionnaire.questionnaire_items)
        return context_items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questionnaire_items'] = self._context_questionnaire_items()
        return context

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('questionnaires', reverse('questionnaires', args=[self.study.slug])),
            (self.questionnaire.number, '')
        ]


class QuestionnaireGenerateView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    generic.TemplateView
):
    title = 'Generate questionnaires'
    template_name = 'lrex_contrib/crispy_formset_form.html'
    formset = None
    helper = None

    def dispatch(self, request, *args, **kwargs):
        self.helper = forms.questionnaire_block_formset_helper(has_exmaple_block=self.study.has_exmaples)
        self.blocks = self.study.item_blocks
        if not self.study.is_allowed_pseudo_randomization:
            messages.info(request, 'Note: Define filler materials to use pseudo randomization.')
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


class QuestionnaireDeleteAllView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    generic.TemplateView
):
    title = 'Confirm Delete'
    template_name = 'lrex_contrib/confirm_delete.html'
    message = 'Delete all questionnaires?'

    def post(self, request, *args, **kwargs):
        self.study.delete_questionnaires()
        messages.success(self.request, 'All questionnaires deleted.')
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


class QuestionnaireBlockInstructionsUpdateView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    contrib_views.LeaveWarningMixin,
    contrib_views.DisableFormMixin,
    generic.TemplateView,
):
    title = 'Edit questionnaire block instructions'
    template_name = 'lrex_contrib/crispy_formset_form.html'
    formset = None
    helper = None

    def dispatch(self, *args, **kwargs):
        self.helper = forms.questionnaire_block_update_formset_helper()
        self.blocks = self.study.item_blocks
        return super().dispatch(*args, **kwargs)

    @property
    def is_disabled(self):
        if self.study.is_active or not self.study.use_blocks:
            return True
        if any(not materials.items_validated for materials in self.study.materials_list):
            return True
        return False

    def get(self, request, *args, **kwargs):
        self.formset = forms.questionnaire_block_update_factory(len(self.blocks))(
            queryset=models.QuestionnaireBlock.objects.filter(study=self.study)
        )
        if not self.study.use_blocks:
            messages.info(request, 'Blocks are disabled for this study.')
        elif any(not materials.items_validated for materials in self.study.materials_list):
            messages.info(request, 'All materials items need to be validated before creating block instructions.')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.formset = forms.questionnaire_block_update_factory(len(self.blocks))(request.POST, request.FILES)
        if self.formset.is_valid():
            self.formset.save(commit=True)
            messages.success(request, 'Block instructions updated.')
            if 'submit' in request.POST:
                return redirect('study', study_slug=self.study.slug)
            else:  # save
                return redirect('questionnaire-blocks', study_slug=self.study.slug)
        return super().get(request, *args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('block-instructions', '')
        ]


class QuestionnaireUploadView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    study_views.DisableFormIfStudyActiveMixin,
    generic.FormView,
):
    title = 'Upload custom questionnaires'
    form_class = forms.QuestionnaireUploadForm
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
        messages.success(self.request, 'Questionnaires uploaded.')
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


class TrialListView(
    study_views.StudyMixin,
    study_views.CheckStudyCreatorMixin,
    contrib_views.ActionsMixin,
    generic.ListView
):
    model = models.Trial
    title = 'Trials'
    paginate_by = 16

    def get(self, request, *args, **kwargs):
        if self.study.has_subject_mapping:
            message = 'Please remove the subject mapping when not needed anymore to reduce the stored personal data.'
            messages.warning(request, message)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action:
            if action == 'download_subjects':
                filename = '{}_SUBJECTS_{}.csv'.format(self.study.title.replace(' ', '_'), str(now().date()))
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
                self.study.subject_mapping_csv(response)
                return response
            elif action == 'delete_subjects':
                self.study.delete_subject_mapping()
                messages.success(request, 'Subject mapping deleted.')
            elif action == 'delete_tests':
                self.study.delete_test_trials()
                messages.success(request, 'All test trials deleted.')
            elif action == 'delete_abandoned':
                self.study.delete_abandoned_trials()
                messages.success(request, 'All abandoned trials deleted.')
        return redirect('trials', study_slug=self.study.slug)

    def get_queryset(self):
        return super().get_queryset().filter(questionnaire__study=self.study)

    @property
    def actions(self):
        if self.study.has_subject_mapping:
            return [
                ('button', 'Download subject ID mapping', 'download_subjects', self.ACTION_CSS_BUTTON_SECONDARY),
                ('button', 'Delete subject ID mapping', 'delete_subjects', self.ACTION_CSS_BUTTON_PRIMARY),
            ]
        return []

    @property
    def secondary_actions(self):
        return [
            ('button', 'Delete tests', 'delete_tests'),
            ('button', 'Delete abandoned', 'delete_abandoned'),
            ('link', 'Delete all', reverse('trials-delete', args=[self.study.slug])),
        ]

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

    def get_success_url(self):
        return reverse('trials', args=[self.study.slug])

    def post(self, request, *args, **kwargs):
        models.Trial.objects.filter(questionnaire__study=self.study).delete()
        messages.success(self.request, 'All trials deleted.')
        return redirect(self.get_success_url())

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('trials', reverse('trials', args=[self.study.slug])),
            ('delete-all', ''),
        ]


class TestTrialMixin:

    @cached_property
    def is_test_trial(self):
        return bool(self.request.GET.get('test', False))

    def get(self, request, *args, **kwargs):
        if self.is_test_trial:
            messages.warning(request, 'Note: This is a test trial.')
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['study'] = self.study
        kwargs['is_test'] = self.is_test_trial
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['is_test'] = self.is_test_trial
        return data


class TestWarningMixin:

    def get(self, request, *args, **kwargs):
        if self.trial.is_test:
            messages.warning(request, 'Note: This is a test trial.')
        return super().get(request, *args, **kwargs)


class TrialIntroView(study_views.StudyMixin, TestTrialMixin, generic.TemplateView):
    template_name = 'lrex_trial/trial_intro.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.study.intro:
            data['intro_rich'] = mark_safe(markdownify(self.study.intro))
        if self.study.privacy_statement:
            data['privacy_statement_rich'] = mark_safe(markdownify(self.study.privacy_statement))
        if self.study.contact_name:
            data['contact'] = mark_safe(self.study.contact_html)
        if self.study.contact_details:
            data['contact_details_rich'] = mark_safe(markdownify(self.study.contact_details))
        data['is_test'] = self.is_test_trial
        return data


class TrialCreateView(study_views.StudyMixin, TestTrialMixin, generic.CreateView):
    model = models.Trial
    form_class = forms.TrialForm
    add_form_kwargs = True

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['instructions_rich'] = mark_safe(markdownify(self.study.instructions))
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
        if self.study.has_demographics:
            return reverse('trial-demographics', args=[self.object.slug])
        if self.study.use_blocks:
            return reverse('rating-block-instructions', args=[self.object.slug, 0])
        return reverse('rating-create', args=[self.object.slug, 0])


class DemographicsCreateView(TrialMixin, TestWarningMixin, generic.TemplateView):
    model = models.Rating
    template_name = 'lrex_trial/trial_demographics.html'

    formset = None
    helper = None

    def dispatch(self, request, *args, **kwargs):
        if self.trial.demographicvalue_set.exists():
            return redirect(reverse('rating-create', args=[self.trial.slug, 0]))
        self.fields_qs = self.study.demographicfield_set
        self.n_fields = self.fields_qs.count()
        self.helper = forms.demographics_formset_helper(self.study.continue_label)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.formset = forms.demographics_formset_factory(self.n_fields, self.n_fields)(
            queryset=models.DemographicValue.objects.none()
        )
        forms.demographics_formset_init(self.formset, self.fields_qs.all())
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        if self.study.use_blocks:
            return reverse('rating-block-instructions', args=[self.object.slug, 0])
        return reverse('rating-create', args=[self.trial.slug, 0])

    def post(self, request, *args, **kwargs):
        self.formset = forms.demographics_formset_factory(self.n_fields)(request.POST, request.FILES)
        if self.formset.is_valid():
            instances = self.formset.save(commit=False)
            for instance in instances:
                instance.trial = self.trial
                instance.save()
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)


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

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.object.slug, reverse('study', args=[self.object.slug])),
            ('delete', ''),
        ]

    def get_success_url(self):
        return reverse('trials', args=[self.study.slug])


class TrialHomeView(study_views.StudyMixin, generic.TemplateView):
    template_name = 'lrex_trial/trial_home.html'


class TrialPrivacyStatementView(study_views.StudyMixin, generic.TemplateView):
    template_name = 'lrex_trial/trial_privacy.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.study.privacy_statement:
            data['privacy_statement_trial_rich'] = mark_safe(markdownify(self.study.privacy_statement))
        data['privacy_statement_lrex_rich'] = mark_safe(markdownify(settings.LREX_PRIVACY_MD))
        return data


class TrialContactView(study_views.StudyMixin, generic.TemplateView):
    template_name = 'lrex_trial/trial_contact.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.study.contact_name:
            data['contact'] = mark_safe(self.study.contact_html)
        if self.study.contact_details:
            data['contact_details_rich'] = mark_safe(markdownify(self.study.contact_details))
        data['contact_lrex_rich'] = mark_safe(markdownify(settings.LREX_CONTACT_MD))
        return data


class TrialInstructionsView(TrialMixin, generic.TemplateView):
    template_name = 'lrex_trial/trial_instructions.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['instructions_rich'] = mark_safe(markdownify(self.study.instructions))
        if self.study.use_blocks and self.study.link_block_instructions:
            questionnaire_block = self.trial.current_block
            data['block_instructions_rich'] = mark_safe(markdownify(questionnaire_block.instructions))
        return data


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


class RatingCreateMixin(ProgressMixin, TestWarningMixin):

    def get_context_data(self, **kwargs):
        kwargs.update(
            {
                'n_trial_items': len(self.trial.items), 'num': self.num,
                'item': self.questionnaire_item.item
            }
        )
        return super().get_context_data(**kwargs)

    def _redirect_to_correct_num(self, num):
        if self.trial.status == models.TrialStatus.FINISHED:
            return reverse('rating-taken', args=[self.trial.slug])
        if self.trial.is_test:
            return None
        try:
            n_ratings = models.Rating.objects.filter(trial=self.trial, question=0).count()
            if n_ratings != num:
                return reverse('rating-create', args=[self.trial.slug, n_ratings])
        except models.Rating.DoesNotExist:
            pass
        return None

    def get_next_url(self):
        trial_items = self.trial.items
        if self.num < len(trial_items) - 1:
            if self.study.use_blocks and \
                    trial_items[self.num].materials_block != trial_items[self.num + 1].materials_block:
                return reverse('rating-block-instructions', args=[self.trial.slug, self.num + 1])
            return reverse('rating-create', args=[self.trial.slug, self.num + 1])
        return reverse('rating-outro', args=[self.trial.slug])

    def _handle_feedbacks(self, ratingforms, instances):
        feedbacks = []
        reload_form_with_feedback = False
        feedbacks_qs = self.questionnaire_item.item.itemfeedback_set
        if feedbacks_qs.count() > 0:
            for i, instance in enumerate(instances):
                question_feedbacks = feedbacks_qs.filter(question=instance.scale_value.question)
                feedbacks_given = ratingforms[i]['feedbacks_given'].value()
                feedbacks_given = [int(f) for f in feedbacks_given.split(',')] if feedbacks_given else []
                show_feedback = None
                for feedback in question_feedbacks:
                    if feedback.pk not in feedbacks_given and feedback.show_feedback(instance.scale_value):
                        reload_form_with_feedback = True
                        show_feedback = feedback
                    feedbacks.append(
                        (i, feedbacks_given, show_feedback)
                    )
        return reload_form_with_feedback, feedbacks


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
        form = self.get_form()
        if form.is_valid():
            show_feedback, feedbacks = self._handle_feedbacks([form], [form.instance])
            if show_feedback:
                rating = form.save(commit=False)
                response = super().get(request)
                form_kwargs = self.get_form_base_kwargs()
                form = self.get_form_class()(**form_kwargs)
                form.fields['scale_value'].initial = rating.scale_value.id
                form.fields['comment'].initial = rating.comment
                for _, feedbacks_given, feedback in feedbacks:
                    form.handle_feedbacks(feedbacks_given, feedback=feedback)
                response.context_data['form'] = form
                messages.error(request, self.study.feedback_message)
                return response
        return super().post(request, *args, **kwargs)

    def get_form_base_kwargs(self):
        kwargs = dict()
        kwargs['study'] = self.study
        kwargs['question'] = self.study.question
        kwargs['questionnaire_item'] = self.questionnaire_item
        if self.item_questions:
            kwargs['item_question'] = self.item_questions[0]
        return kwargs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(**self.get_form_base_kwargs())
        return kwargs

    def form_valid(self, form):
        form.instance.trial = self.trial
        form.instance.questionnaire_item = self.questionnaire_item
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
        forms.ratingformset_init(
            self.formset,
            self.study,
            self.item_questions,
            self.questionnaire_item,
        )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.questionnaire_item.rating_set.filter(trial=self.trial).exists():
            return redirect(self.get_next_url())
        self.formset = forms.ratingformset_factory(self.n_questions)(request.POST, request.FILES)
        forms.ratingformset_init(
            self.formset,
            self.study,
            self.item_questions,
            self.questionnaire_item,
        )
        if self.formset.is_valid():
            instances = self.formset.save(commit=False)
            if len(instances) < self.n_questions or any(form['scale_value'].value() is None for form in self.formset):
                response = self.get(request, *args, **kwargs)
                for instance in instances:
                    if hasattr(instance, 'scale_value'):
                        self.formset[instance.question].fields['scale_value'].initial = instance.scale_value.pk
                    if hasattr(instance, 'comment'):
                        self.formset[instance.question].fields['comment'].initial = instance.comment
                messages.error(request, self.study.answer_questions_message)
                return response
            elif self.study.enable_item_rating_feedback:
                    show_feedback, feedbacks = self._handle_feedbacks(self.formset, instances)
                    if show_feedback:
                        response = self.get(request, *args, **kwargs)
                        for instance in instances:
                            self.formset[instance.question].fields['scale_value'].initial = instance.scale_value.pk
                        show_feedback = forms.ratingformset_handle_feedbacks(self.formset, feedbacks)
                        if show_feedback:
                            messages.error(request, self.study.feedback_message)
                        return response
            for instance in instances:
                instance.trial = self.trial
                instance.questionnaire_item = self.questionnaire_item
                instance.save()
            return redirect(self.get_next_url())
        return super().get(request, *args, **kwargs)


class RatingBlockInstructionsView(ProgressMixin, TestWarningMixin, TrialMixin, generic.TemplateView):
    template_name = 'lrex_trial/rating_block_instructions.html'

    def get_context_data(self, **kwargs):
        kwargs.update(
            {'n_trial_items': len(self.trial.items)}
        )
        data = super().get_context_data(**kwargs)
        questionnaire_block = self.trial.current_block
        data['block_instructions_rich'] = mark_safe(markdownify(questionnaire_block.instructions))
        data['trial'] = self.trial
        return data


class RatingOutroView(TrialMixin, TestWarningMixin, generic.TemplateView):
    template_name = 'lrex_trial/rating_outro.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if not self.study.require_participant_id:
            data['subject_id'] = self.trial.subject_id
        data['outro_rich'] = mark_safe(markdownify(self.study.outro))
        return data


class RatingTakenView(TrialMixin, TestWarningMixin, generic.TemplateView):
    template_name = 'lrex_trial/rating_taken.html'
