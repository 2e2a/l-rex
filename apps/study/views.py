from tempfile import TemporaryFile

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views import generic

from apps.contrib import views as contib_views
from apps.contrib.utils import split_list_string

from . import models
from . import forms


class WarnUserIfStudyActiveMixin:

    def get(self, request, *args, **kwargs):
        if self.study.is_active or self.study.is_finished:
            if hasattr(self, 'form_valid') or hasattr(self, 'helper'):
                msg = 'Note: Form is disabled. '
            else:
                msg = 'Note: Some actions are disabled. '
            msg += 'To enable editing, '
            if self.study.is_published:
                msg += '<a href="{}">set study status to draft</a>'\
                    .format(
                        reverse('study', args=[self.study.slug]),
                    )
                msg += ' and ' if self.study.trial_count > 0 else '.'
            if self.study.trial_count > 0:
                msg += '<a href="{}">save and remove the results</a>.'\
                    .format(
                        reverse('trials', args=[self.study.slug])
                    )
            messages.info(request, mark_safe(msg))
        return super().get(request, *args, **kwargs)


class DisableFormIfStudyActiveMixin(WarnUserIfStudyActiveMixin, contib_views.DisableFormMixin):

    @property
    def is_disabled(self):
        return self.study.is_active or self.study.is_finished


class NextStepsMixin:

    def _steps_html(self, steps, study_url):
        for group, group_steps in steps.items():
            if not group_steps:
                continue
            steps = []
            for description, url in group_steps:
                steps.append((url, description))
            group_steps_context = {
                'group': group,
                'group_steps': steps,
            }
            step_html = render_to_string('lrex_study/study_steps.html', group_steps_context)
            yield mark_safe(step_html)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        study_url = self.study.get_absolute_url()
        next_steps = self.study.next_steps()
        next_steps_html = self._steps_html(next_steps, study_url)
        optional_steps = self.study.optional_steps()
        optional_steps_html = self._steps_html(optional_steps, study_url)
        context.update({
            'next_steps_html': next_steps_html,
            'optional_steps_html': optional_steps_html,
        })
        return context


class StudyMixin:
    slug_url_kwarg = 'study_slug'
    study_object = None

    @property
    def study(self):
        if not self.study_object:
            study_slug = self.kwargs['study_slug']
            self.study_object = models.Study.objects.get(slug=study_slug)
        return self.study_object

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['study'] = self.study
        return data


class StudyObjectMixin(StudyMixin):

    @property
    def study(self):
        if not self.study_object:
            self.study_object =  self.get_object()
        return self.study_object


class CheckStudyCreatorMixin(UserPassesTestMixin):

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user == self.study.creator:
            return True
        if self.study.shared_with and self.request.user.username in self.study.shared_with:
            return True
        if self.request.user.is_superuser:
            return True
        return False


class SettingsNavMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nav_active'] = 1
        return context


class TasksNavMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nav_active'] = 2
        return context


class MaterialsNavMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nav_active'] = 3
        if hasattr(self, 'materials'):
            context['active_materials'] = self.materials.pk
        return context


class QuestionnaireNavMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nav_active'] = 4
        return context


class PrivacyNavMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nav_active'] = 5
        return context


class ResultsNavMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nav_active'] = 6
        return context


class StudyListView(LoginRequiredMixin, generic.ListView):
    model = models.Study
    title = 'Studies'
    paginate_by = 16

    def get(self, request, *args, **kwargs):
        if not hasattr(self.request.user, 'userprofile'):
            return redirect('user-profile-create')
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(
            Q(creator=self.request.user) |
            Q(shared_with__contains=self.request.user.username)
        )


class StudyCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Study
    title = 'Create a new study'
    template_name = 'lrex_home/base_form.html'
    form_class = forms.StudyForm

    def form_valid(self, form):
        form.instance.creator = self.request.user
        response = super().form_valid(form)
        message = 'Study successfully created. Below on the dashboard, you will see suggestions what to do next. ' \
                  'They will point you to steps that need to be completed while setting up your study. ' \
                  'For more detailed help, consult the <a href="https://github.com/2e2a/l-rex/wiki">Wiki</a>.'
        messages.info(self.request, mark_safe(message))
        return response


class StudyDetailView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    NextStepsMixin,
    generic.DetailView,
):
    model = models.Study
    template_name = 'lrex_study/study_dashboard.html'

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action == 'draft':
            self.study.is_published = False
            self.study.is_finished = False
            messages.success(request, 'Study status changed to draft.')
        elif action == 'published':
            self.study.is_published = True
            self.study.is_finished = False
            messages.success(request, 'Study status changed to published.')
        elif action == 'finished':
            self.study.is_published = False
            self.study.is_finished = True
            messages.success(request, 'Study status changed to finished.')
        self.study.save()
        return redirect('study', study_slug=self.study.slug)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data.update({
            'allow_publish': self.study.is_allowed_publish,
            'trial_count_active': self.study.trial_count_active,
            'trial_count_finished': self.study.trial_count_finished,
            'trial_count_abandoned': self.study.trial_count_abandoned,
            'trial_count_test': self.study.trial_count_test,
            'materials_ready': [],
            'materials_draft': [],
        })
        for materials in self.study.materials.all():
            data['materials_ready' if materials.is_complete else 'materials_draft'].append(materials)
        return data


class StudyDeleteView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    contib_views.DefaultDeleteView
):
    model = models.Study
    template_name = 'lrex_home/base_confirm_delete.html'

    def get_success_url(self):
        return reverse('studies')


class StudyArchiveView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    generic.UpdateView
):
    model = models.Study
    template_name = 'lrex_study/study_archive.html'
    form_class = forms.ArchiveForm
    title = 'Archive the study'

    def get_success_url(self):
        import pdb;pdb.set_trace()
        return reverse('studies')

    def get(self, request, *args, **kwargs):
        if self.study.has_subject_mapping:
            download_link = (
                '<a href="{}">download subject-ID mapping</a>'
            ).format(reverse('trials-subjects-download', args=[self.study.slug]))
            msg = 'Please {} first, if needed. It is not included in the archive.'.format(download_link)
            messages.warning(request, mark_safe(msg))
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        self.study.archive()
        return super().form_valid(form)


class StudyArchiveDownloadView(StudyObjectMixin, CheckStudyCreatorMixin, generic.DetailView):
    model = models.Study

    def get(self, request, *args, **kwargs):
        filename = '{}_ARCHIVE_{}.zip'.format(self.study.title.replace(' ', '_'), str(now().date()))
        response = HttpResponse(content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        self.study.archive_file(response)
        return response


class StudyCreateFromArchiveView(LoginRequiredMixin,  SuccessMessageMixin, generic.FormView):
    title = 'Create a new study from archive'
    template_name = 'lrex_home/base_form.html'
    form_class = forms.StudyNewFromArchiveForm

    def get(self, request, *args, **kwargs):
        messages.info(self.request, 'Note: Please be patient, this might take a while.')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        super().form_valid(form)
        title = form['title'].value()
        file = form['file'].value()
        try:
            study = models.Study.create_from_archive_file(file, self.request.user)
            study.title = title
            study.save()
            messages.success(self.request, 'Study successfully created.')
            return redirect('study', study_slug=study.slug)
        except Exception as err:
            if settings.DEBUG:
                raise err
            messages.error(
                self.request,
                'An error occured during study creation. Please check the new study and contact the admin.'
            )
        return redirect('studies')

    def get_success_url(self):
        return reverse('studies', args=[])


class StudyRestoreFromArchiveView(StudyMixin, CheckStudyCreatorMixin, SuccessMessageMixin, generic.FormView):
    title = 'Restore study from archive'
    template_name = 'lrex_home/base_form.html'
    form_class = forms.StudyFromArchiveForm

    def get(self, request, *args, **kwargs):
        messages.info(self.request, 'Note: Please be patient, restoring a study might take a while.')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        file = form['file'].value()
        try:
            self.study.restore_from_archive(file)
            messages.success(self.request, 'Study successfully restored.')
        except Exception as err:
            self.study.archive()
            if settings.DEBUG:
                raise err
            messages.error(
                self.request,
                'An error occured during study creation. Please check the new study and contact the admin.'
            )
        return response

    def get_success_url(self):
        return reverse('study', args=[self.study.slug])


class StudyCreateCopyView(StudyMixin, CheckStudyCreatorMixin, SuccessMessageMixin, generic.FormView):
    title = 'Create a copy of a study'
    template_name = 'lrex_home/base_form.html'
    form_class = forms.StudyCopyForm
    success_message = 'Study successfully created.'

    def get(self, request, *args, **kwargs):
        messages.info(self.request, 'Note: Please be patient, this might take a while.')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        super().form_valid(form)
        title = form['title'].value()
        file = TemporaryFile()
        try:
            self.study.archive_file(file)
            study = models.Study.create_from_archive_file(file, self.request.user)
        except:
            messages.error(
                self.request,
                'An error occured during study creation. Please check the new study and contact the admin.'
            )
        study.title = title
        study.save()
        return redirect('study', study_slug=study.slug)

    def get_success_url(self):
        return reverse('studies', args=[])


class StudySettingsView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    SettingsNavMixin,
    generic.UpdateView,
):
    model = models.Study
    title = 'Study settings'
    template_name = 'lrex_study/study_settings.html'
    form_class = forms.StudySettingsForm
    success_message = 'Study settings updated.'

    def get(self, request, *args, **kwargs):
        if not self.is_disabled:
            if self.study.has_items:
                msg = 'Note: To change the "item type" setting you would need to remove items first.'
                messages.info(request, msg)
            if self.study.has_questionnaires:
                msg = 'Note: To change the "Use blocks" and "Randomize question order" settings you would need to ' \
                      '<a href="{}">remove questionnaires </a> first.'.format(
                        reverse('questionnaires', args=[self.study.slug]))
                messages.info(request, mark_safe(msg))
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'add_save': True,
            'disable_itemtype': self.study.has_items,
            'disable_randomize_question_order': self.study.has_questionnaires,
            'disable_use_blocks': self.study.has_questionnaires,
            'disable_feedback': self.study.is_active,
        })
        return kwargs

    def get_success_url(self):
        if 'save' in self.request.POST:
            return reverse('study-settings', args=[self.object.slug])
        return self.object.get_absolute_url()


class StudySettingsDeleteView(
    SettingsNavMixin,
    StudyDeleteView,
):
    template_name = 'lrex_dashboard/settings_confirm_delete.html'


class StudySettingsArchiveView(
    SettingsNavMixin,
    StudyArchiveView,
):
    template_name = 'lrex_study/study_archive_settings.html'


class StudyLabelsUpdateView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    SettingsNavMixin,
    generic.UpdateView,
):
    model = models.Study
    title = 'Customize labels'
    template_name = 'lrex_dashboard/settings_form.html'
    form_class = forms.StudyLabelsForm
    success_message = 'Labels updated.'

    def get(self, request, *args, **kwargs):
        msg = 'Note: Translatable elements are not shown when the respective feature is disabled via a study or ' \
              'a question setting.'
        messages.info(request, msg)
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'study': self.study,
            'add_save': True,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'nav2_active': 1,
        })
        return context

    def get_success_url(self):
        if 'save' in self.request.POST:
            return reverse('study-labels', args=[self.object.slug])
        return self.object.get_absolute_url()


class StudyShareView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    contib_views.LeaveWarningMixin,
    SettingsNavMixin,
    generic.UpdateView
):
    model = models.Study
    title = 'Share the study'
    form_class = forms.SharedWithForm
    template_name = 'lrex_dashboard/settings_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'add_save': True,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'nav2_active': 2,
        })
        return context

    def get_success_url(self):
        if 'save' in self.request.POST:
            return reverse('study-share', args=[self.object.slug])
        return self.object.get_absolute_url()


class QuestionUpdateView(
    StudyMixin,
    CheckStudyCreatorMixin,
    contib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    TasksNavMixin,
    generic.DetailView,
):
    model = models.Study
    title = 'Questions'
    template_name = 'lrex_dashboard/tasks_formset_form.html'
    formset = None
    helper = None

    @property
    def is_disabled(self):
        if self.study.is_active:
            return True
        if self.study.has_item_questions:
            return True
        return False

    def dispatch(self, *args, **kwargs):
        self.helper = forms.question_formset_helper()
        self.n_questions = self.study.questions.count()
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        if not self.is_disabled:
            if self.study.has_item_questions:
                msg = 'Note: To change questions you need to remove items with custom questions first.'
                messages.info(request, mark_safe(msg))
            if self.study.has_questionnaires:
                msg = 'Note: To change the "randomize scale" settings you need to ' \
                      '<a href="{}">remove questionnaires</a> first.'.format(
                    reverse('questionnaires', args=[self.study.slug]))
                messages.info(request, mark_safe(msg))
        self.formset = forms.question_formset_factory(self.n_questions, 0 if self.n_questions > 0 else 1)(
            queryset=self.study.questions.all()
        )
        forms.initialize_with_questions(self.formset, self.study.questions.all())
        forms.question_formset_disable_fields(
            self.formset,
            disable_randomize_scale=self.study.has_questionnaires,
        )
        return super().get(request, *args, **kwargs)

    def _invalidate_materials_items(self):
        for materials in self.study.materials.all():
            materials.set_items_validated(False)

    def post(self, request, *args, **kwargs):
        self.formset = forms.question_formset_factory(self.n_questions)(request.POST, request.FILES)
        if self.formset.is_valid():
            instances = self.formset.save(commit=False)
            for i, (instance, form) in enumerate(zip(instances, self.formset)):
                instance.study = self.study
                instance.number = i
                instance.save()
                scale_values_new = []
                scale_values_old = list(instance.scalevalues.all())
                scale_labels = split_list_string(form.cleaned_data['scale_labels'])
                for j, scale_label in enumerate(scale_labels):
                    if scale_label:
                        scale_value, created = models.ScaleValue.objects.get_or_create(
                            number=j,
                            question=instance,
                            label=scale_label,
                        )
                        if created:
                            scale_values_new.append(scale_value)
                        else:
                            scale_values_old.remove(scale_value)
                if scale_values_old or scale_values_new and self.study.has_item_questions:
                    self._invalidate_materials_items()
                for scale_value in scale_values_old:
                    scale_value.delete()
            self.n_questions = self.study.questions.count()
            extra = len(self.formset.forms) - self.n_questions
            if 'submit' in request.POST:
                messages.success(request, 'Questions saved.')
                return redirect('study', study_slug=self.study.slug)
            elif 'save' in request.POST:
                messages.success(request, 'Questions saved.')
            elif 'add' in request.POST:
                self.formset = forms.question_formset_factory(self.n_questions, extra + 1)(
                    queryset=models.Question.objects.filter(study=self.study)
                )
            else: # delete last
                if extra > 0:
                    extra -= 1
                elif self.n_questions > 0:
                    self.study.questions.last().delete()
                    if self.study.has_item_questions:
                        self._invalidate_materials_items()
                    self.n_questions -= 1
                self.formset = forms.question_formset_factory(self.n_questions, extra)(
                    queryset=models.Question.objects.filter(study=self.study)
                )
            forms.initialize_with_questions(self.formset, self.study.questions.all())
            forms.question_formset_disable_fields(
                self.formset,
                disable_randomize_scale=self.study.has_questionnaires,
            )
        return super().get(request, *args, **kwargs)


class StudyInstructionsUpdateView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    TasksNavMixin,
    generic.UpdateView,
):
    model = models.Study
    title ='Instructions'
    template_name = 'lrex_dashboard/tasks_form.html'
    form_class = forms.StudyInstructionsForm
    success_message = 'Instructions saved.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'add_save': True,
        })
        return kwargs

    def get_success_url(self):
        if 'save' in self.request.POST:
            return reverse('study-instructions', args=[self.object.slug])
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'nav2_active': 1,
        })
        return context


class StudyIntroUpdateView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    TasksNavMixin,
    generic.UpdateView,
):
    model = models.Study
    title = 'Intro/outro'
    template_name = 'lrex_dashboard/tasks_form.html'
    form_class = forms.StudyIntroForm
    success_message = 'Intro/outro saved.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'add_save': True,
        })
        return kwargs

    def get_success_url(self):
        if 'save' in self.request.POST:
            return reverse('study-intro', args=[self.object.slug])
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'nav2_active': 2,
        })
        return context


class DemographicsUpdateView(
    StudyMixin,
    CheckStudyCreatorMixin,
    contib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    TasksNavMixin,
    generic.DetailView,
):
    model = models.Study
    title = 'Demographics'
    template_name = 'lrex_dashboard/tasks_formset_form.html'
    formset = None
    helper = None

    def dispatch(self, *args, **kwargs):
        self.helper = forms.demographic_formset_helper()
        self.n_fields = self.study.demographics.count()
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        msg = 'Please respect the privacy of your participants. Do not collect private data that you do not need.'
        messages.warning(self.request, msg)
        self.formset = forms.demographic_formset_factory(self.n_fields, 0 if self.n_fields > 0 else 1)(
            queryset=self.study.demographics.all()
        )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.formset = forms.demographic_formset_factory(self.n_fields)(request.POST, request.FILES)
        if self.formset.is_valid():
            instances = self.formset.save(commit=False)
            for i, (instance, form) in enumerate(zip(instances, self.formset)):
                instance.study = self.study
                instance.number = i
                instance.save()
            self.n_fields = self.study.demographics.count()
            extra = len(self.formset.forms) - self.n_fields
            if 'submit' in request.POST:
                messages.success(request, 'Demographics saved.')
                return redirect('study', study_slug=self.study.slug)
            elif 'save' in request.POST:
                messages.success(request, 'Demographics saved.')
                self.formset = forms.demographic_formset_factory(self.n_fields, extra)(
                    queryset=self.study.demographics.all()
                )
            elif 'add' in request.POST:
                self.formset = forms.demographic_formset_factory(self.n_fields, extra + 1)(
                    queryset=self.study.demographics.all()
                )
            else: # delete last
                if extra > 0:
                    extra -= 1
                elif self.n_fields > 0:
                    self.study.demographics.last().delete()
                    self.n_fields -= 1
                self.formset = forms.demographic_formset_factory(self.n_fields, extra)(
                    queryset=self.study.demographics.all()
                )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'nav2_active': 3,
        })
        return context


class StudyContactUpdateView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    PrivacyNavMixin,
    generic.UpdateView,
):
    model = models.Study
    title = 'Contact information'
    template_name = 'lrex_dashboard/privacy_form.html'
    form_class = forms.StudyContactForm
    success_message = 'Contact information saved.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'add_save': True,
        })
        return kwargs

    def get_success_url(self):
        if 'save' in self.request.POST:
            return reverse('study-contact', args=[self.object.slug])
        return self.object.get_absolute_url()


class StudyPrivacyUpdateView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    PrivacyNavMixin,
    generic.UpdateView,
):
    model = models.Study
    title = 'Privacy statement'
    template_name = 'lrex_dashboard/privacy_form.html'
    form_class = forms.StudyPrivacyForm
    success_message = 'Privacy statement saved.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'add_save': True,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'nav2_active': 1,
        })
        return context

    def get_success_url(self):
        if 'save' in self.request.POST:
            return reverse('study-privacy', args=[self.object.slug])
        return self.object.get_absolute_url()


class StudyResultsCSVDownloadView(StudyObjectMixin, CheckStudyCreatorMixin, generic.DetailView):
    model = models.Study

    def get(self, request, *args, **kwargs):
        filename = '{}_RESULTS_{}.csv'.format(self.study.title.replace(' ', '_'), str(now().date()))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        self.study.results_csv(response)
        return response

