from tempfile import TemporaryFile

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views import generic

from apps.contrib import views as contrib_views
from apps.contrib.utils import split_list_string

from . import models
from . import forms


class WarnUserIfStudyActiveMixin:

    def get(self, request, *args, **kwargs):
        if self.study.is_active or self.study.is_finished:
            if hasattr(self, 'form_valid') or hasattr(self, 'formset'):
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


class DisableFormIfStudyActiveMixin(WarnUserIfStudyActiveMixin, contrib_views.DisableFormMixin):

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

    @cached_property
    def study(self):
        if not self.study_object:
            study_slug = self.kwargs['study_slug']
            try:
                self.study_object = models.Study.objects.get(slug=study_slug)
            except models.Study.DoesNotExist:
                raise Http404()
        return self.study_object

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['study'] = self.study
        return data


class StudyObjectMixin(StudyMixin):

    @cached_property
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
        if self.study.shared_with and self.request.user in self.study.shared_with.all():
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


class StudyListView(LoginRequiredMixin, contrib_views.PaginationHelperMixin, generic.ListView):
    model = models.Study
    title = 'Studies'
    paginate_by = 16

    filter_sort_form = None

    sort_by = 'date'
    show_archived = False

    def get(self, request, *args, **kwargs):
        if not hasattr(self.request.user, 'userprofile'):
            return redirect('user-account-create')
        is_filtered = 'submit' in self.request.GET
        self.sort_by = self.request.GET.get('sort_by', 'date')
        self.show_archived = is_filtered and self.request.GET.get('archived', False)
        self.show_shared = not is_filtered or self.request.GET.get('shared', False)
        self.filter_sort_form = forms.StudyFilterSortForm(
            sort_by=self.sort_by,
            archived=self.show_archived,
            shared=self.show_shared,
        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'filter_sort_form': self.filter_sort_form,
        })
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.show_shared:
            queryset = queryset.filter(creator=self.request.user)
        else:
            queryset = queryset.filter(
                Q(creator=self.request.user) |
                Q(shared_with=self.request.user)
            ).distinct()
        if not self.show_archived:
            queryset = queryset.filter(is_archived=False)
        if self.sort_by == 'name':
            queryset = queryset.order_by('title', 'created_date')
        queryset = queryset.prefetch_related(
            'creator',
        )
        return queryset


class StudyCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Study
    title = 'Create a new study'
    template_name = 'base_form.html'
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

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.prefetch_related(
            'questions',
            'materials',
            'materials__items',
            'materials__lists',
            'questionnaires',
        )
        return queryset

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
    contrib_views.PaginationHelperMixin,
    contrib_views.DefaultDeleteView
):
    model = models.Study
    template_name = 'base_confirm_delete.html'

    def get_success_url(self):
        return self.reverse_paginated('studies')


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
        return reverse('studies')

    def get(self, request, *args, **kwargs):
        if self.study.has_participant_information:
            download_link = (
                '<a href="{}">download participant information</a>'
            ).format(reverse('trials-participants-download', args=[self.study.slug]))
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
    template_name = 'base_form.html'
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
    template_name = 'base_form.html'
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
    template_name = 'base_form.html'
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
    contrib_views.LeaveWarningMixin,
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
    contrib_views.LeaveWarningMixin,
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
        msg = (
            'Note: Customizable elements are not shown when the respective feature is disabled via a study or a '
            'question setting.'
        )
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
    StudyMixin,
    CheckStudyCreatorMixin,
    contrib_views.LeaveWarningMixin,
    SettingsNavMixin,
    generic.FormView
):
    model = models.Study
    title = 'Share the study'
    form_class = forms.SharedWithForm
    template_name = 'lrex_study/study_share.html'

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action == 'unsubscribe':
            self.study.shared_with.remove(request.user)
            self.study.save()
            messages.success(request, 'Unsubscribed from shared study.')
            return redirect('studies')
        return super().post(request, *args, **kwargs)

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
            'nav2_active': 2,
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        user_names = [user_name for user_name in form.cleaned_data['shared_with'].split(',')]
        users = User.objects.filter(username__in=user_names)
        self.study.shared_with.set(users)
        self.study.save()
        return response

    def get_success_url(self):
        if 'save' in self.request.POST:
            return reverse('study-share', args=[self.study.slug])
        return self.study.get_absolute_url()


class QuestionUpdateView(
    StudyMixin,
    CheckStudyCreatorMixin,
    contrib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    TasksNavMixin,
    contrib_views.FormsetView,
):
    model = models.Study
    title = 'Questions'
    template_name = 'lrex_dashboard/tasks_formset_form.html'
    formset_factory = forms.QuestionFormsetFactory

    def get_formset_queryset(self):
        return self.study.questions.all()

    def submit_redirect(self):
        return redirect('study', study_slug=self.study.slug)

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
        return super().get(request, *args, **kwargs)

    def _invalidate_materials_items(self):
        for materials in self.study.materials.all():
            materials.set_items_validated(False)

    def save_form(self, form, number):
        form.instance.study = self.study
        form.instance.number = number
        super().save_form(form, number)
        scale_values = []
        number_changed = False
        scale_values_old_count = form.instance.scale_values.all().count()
        scale_labels = split_list_string(form.cleaned_data['scale_labels'])
        scale_values_count = len(scale_labels)
        if scale_values_old_count > scale_values_count:
            n_deleted_scales = scale_values_old_count - scale_values_count
            form.instance.scale_values.all()[n_deleted_scales:].delete()
            number_changed = True
        for j, scale_label in enumerate(scale_labels):
            if scale_label:
                scale_value, created = models.ScaleValue.objects.get_or_create(
                    number=j,
                    question=form.instance,
                )
                scale_value.label = scale_label
                scale_values.append(scale_value)
                if created:
                    number_changed = True
        if number_changed and self.study.has_item_questions:
            self._invalidate_materials_items()
        for scale_value in scale_values:
            scale_value.save()


class StudyInstructionsUpdateView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contrib_views.LeaveWarningMixin,
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
    contrib_views.LeaveWarningMixin,
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
    contrib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    TasksNavMixin,
    contrib_views.FormsetView,
):
    model = models.Study
    title = 'Demographics'
    template_name = 'lrex_dashboard/tasks_formset_form.html'
    formset_factory = forms.DemographicsFormsetFactory

    def get_formset_queryset(self):
        return self.study.demographics.all()

    def submit_redirect(self):
        return redirect('study', study_slug=self.study.slug)

    def get(self, request, *args, **kwargs):
        msg = 'Please respect the privacy of your participants. Do not collect private data that you do not need.'
        messages.warning(self.request, msg)
        return super().get(request, *args, **kwargs)

    def save_form(self, form, number):
        form.instance.study = self.study
        form.instance.number = number
        super().save_form(form, number)

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
    contrib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    PrivacyNavMixin,
    generic.UpdateView,
):
    model = models.Study
    title = 'Contact information'
    template_name = 'lrex_dashboard/info_form.html'
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


class StudyConsentUpdateView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contrib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    PrivacyNavMixin,
    generic.UpdateView,
):
    model = models.Study
    title = 'Consent form'
    template_name = 'lrex_dashboard/info_form.html'
    form_class = forms.StudyConsentForm
    success_message = 'Consent form saved.'

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
            return reverse('study-consent', args=[self.object.slug])
        return self.object.get_absolute_url()


class StudyResultsCSVDownloadView(StudyObjectMixin, CheckStudyCreatorMixin, generic.DetailView):
    model = models.Study

    def get(self, request, *args, **kwargs):
        filename = '{}_RESULTS_{}.csv'.format(self.study.title.replace(' ', '_'), now().strftime('%Y-%m-%d-%H%M'))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        self.study.results_csv(response)
        return response
