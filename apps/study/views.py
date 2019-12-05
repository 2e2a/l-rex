from tempfile import TemporaryFile

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

from . import models
from . import forms


class WarnUserIfStudyActiveMixin:

    def get(self, request, *args, **kwargs):
        if self.study.is_active:
            if hasattr(self, 'form_valid') or hasattr(self, 'helper'):
                msg = 'Note: Form is disabled. '
            else:
                msg = 'Note: Some actions are disabled. '
            msg = msg + 'You cannot change an active study. Please <a href="{}">unpublish</a> ' \
                        'the study and save and <a href="{}">remove the results</a> first.'\
                        .format(
                            reverse('study', args=[self.study.slug]),
                            reverse('trials', args=[self.study.slug])
                        )
            messages.info(request, mark_safe(msg))
        return  super().get(request, *args, **kwargs)


class DisableFormIfStudyActiveMixin(WarnUserIfStudyActiveMixin, contib_views.DisableFormMixin):

    @property
    def is_disabled(self):
        return self.study.is_active


class NextStepsMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        next_steps_html = []
        next_steps = self.study.next_steps()
        step_html_template = '<a href="{}">{}</a>'
        steps_html_template = '<div class="d-flex justify-content-between">\n' \
                              '    <span>{}</span>\n' \
                              '    <span class="text-right text-secondary"><small><em>{}</em></small></span>\n' \
                              '</div>'
        for group, group_steps in next_steps.items():
            if not group_steps:
                continue
            steps = [step_html_template.format(url, description) for description, url in group_steps]
            step_html = steps_html_template.format('<br/>'.join(steps), group)
            next_steps_html.append(mark_safe(step_html))
        optional_steps_html = [
            mark_safe(steps_html_template.format(
                '<br/>'.join([
                    step_html_template.format(
                        reverse('study-settings', args=[self.study.slug]), 'Customize study settings'
                    ),
                    step_html_template.format(
                        reverse('study-translate', args=[self.study.slug]), 'Translate build-in texts'
                    )
                ]),
                'Settings',
            )),
        ] if not self.study.is_published else []
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


class NavMixin:
    nav = []
    nav_active = 0
    secondary_nav = []
    secondary_nav_active = 0

    def _nav_html(self, nav_type, nav, is_active):
        nav_context = {
            'type': nav_type,
            'active': is_active,
        }
        if nav_type == 'link':
            name, url = nav
            nav_context.update({
                'name': name,
                'url': url
            })
        elif nav_type == 'dropdown':
            name, urls = nav
            nav_context.update({
                'name': name,
                'urls': urls,
            })
        return render_to_string('lrex_study/study_nav.html', nav_context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'nav': [self._nav_html(nav_type, nav_item, i == self.nav_active)
                    for i, (nav_type, nav_item) in enumerate(self.nav)],
            'secondary_nav': [self._nav_html(nav_type, nav_item, i == self.secondary_nav_active)
                        for i, (nav_type, nav_item) in enumerate(self.secondary_nav)],
        })
        return context


class StudyNavMixin(NavMixin):

    @property
    def materials_nav(self):
        return [
            (materials.title, reverse('items', args=[materials.slug])) for materials in self.study.materials_list
        ] + [
            (None, None),  # separator
            ('New materials', reverse('materials-create', args=[self.study.slug])),
        ]

    @property
    def nav(self):
        return [
            ('link', ('Dashboard', reverse('study', args=[self.study.slug]))),
            ('link', ('Settings', reverse('study-settings', args=[self.study.slug]))),
            ('link', ('Task and instructions', reverse('study-questions', args=[self.study.slug]))),
            ('dropdown', ('Materials', self.materials_nav)),
            ('link', ('Questionnaires', reverse('questionnaires', args=[self.study.slug]))),
            ('link', ('Contact and privacy', reverse('study-contact', args=[self.study.slug]))),
            ('link', ('Results', reverse('trials', args=[self.study.slug]))),
        ]


class StudyListView(LoginRequiredMixin, contib_views.ActionsMixin, generic.ListView):
    model = models.Study
    title = 'Studies'
    paginate_by = 16

    def get_queryset(self):
        return super().get_queryset().filter(
            Q(creator=self.request.user) |
            Q(shared_with__contains=self.request.user.username)
        )

    @property
    def actions(self):
        return [
            ('link', 'New study', reverse('study-create'), self.ACTION_CSS_BUTTON_PRIMARY)
        ]

    @property
    def secondary_actions(self):
        return [
            ('link', 'New study from archive', reverse('study-create-archive'))
        ]

    @property
    def breadcrumbs(self):
        return [
            ('studies', ''),
        ]


class StudyCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Study
    title = 'Create study'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.StudyForm

    def form_valid(self, form):
        form.instance.creator = self.request.user
        response = super().form_valid(form)
        message = 'Study successfully created. Below, on the dashboard you will see suggestions what to do next. ' \
                  'They will point you to steps that need to be completed while setting up your study. ' \
                  'For more detailed help, consult the <a href="https://github.com/2e2a/l-rex/wiki">Wiki</a>.'
        messages.info(self.request, mark_safe(message))
        return response

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            ('new', ''),
        ]


class StudyCreateFromArchiveView(LoginRequiredMixin,  SuccessMessageMixin, generic.FormView):
    title = 'Create a new study from archive'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.StudyFromArchiveForm
    success_message = 'Study successfully created.'

    def get(self, request, *args, **kwargs):
        messages.info(self.request, 'Note: Please be patient, this might take a while.')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        super().form_valid(form)
        file = form['file'].value()
        study = models.Study.create_from_archive_file(file, self.request.user)
        return redirect('study', study_slug=study.slug)

    def get_success_url(self):
        return reverse('studies', args=[])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            ('new from archive', ''),
        ]


class StudyDetailView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    contib_views.ActionsMixin,
    StudyNavMixin,
    NextStepsMixin,
    generic.DetailView,
):
    model = models.Study

    @property
    def title(self):
        return self.study.title

    def get(self, request, *args, **kwargs):
        if not hasattr(self.request.user, 'userprofile'):
            return redirect('user-profile-create')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action == 'publish':
            self.study.is_published = True
            messages.success(request, 'Study published.')
            self.study.save()
        elif action == 'unpublish':
            self.study.is_published = False
            messages.success(request, 'Study unpublished.')
            self.study.save()
        return redirect('study', study_slug=self.study.slug)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['allow_publish'] = self.study.is_allowed_publish
        data['trial_count_active'] = self.study.trial_count_active
        data['trial_count_finished'] = self.study.trial_count_finished
        data['trial_count_abandoned'] = self.study.trial_count_abandoned
        data['trial_count_test'] = self.study.trial_count_test
        data['materials_ready'] = []
        data['materials_draft'] = []
        for materials in self.study.materials_list:
            data['materials_ready' if materials.is_complete else 'materials_draft'].append(materials)
        return data

    @property
    def actions(self):
        actions = []
        if not self.study.is_published:
            actions.append(('button', 'Publish', 'publish', self.ACTION_CSS_BUTTON_PRIMARY))
        else:
            actions.append(('button', 'Unpublish', 'unpublish', self.ACTION_CSS_BUTTON_WARNING))
        return actions

    @property
    def secondary_actions(self):
        return [
            ('link', 'Settings', reverse('study-settings', args=[self.study.slug])),
            ('link', 'Translations', reverse('study-translate', args=[self.study.slug])),
            ('link', 'Share', reverse('study-share', args=[self.study.slug])),
            ('link', 'Archive', reverse('study-archive', args=[self.study.slug])),
            ('link', 'Delete', reverse('study-delete', args=[self.study.slug])),
        ]

    @property
    def disable_actions(self):
        if not self.study.is_published and not self.study.is_allowed_publish:
            return [0], []

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, ''),
        ]


class StudyDeleteView(StudyObjectMixin, CheckStudyCreatorMixin, contib_views.DefaultDeleteView):
    model = models.Study

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('delete', ''),
        ]

    def get_success_url(self):
        return reverse('studies')


class StudyArchiveView(StudyObjectMixin, CheckStudyCreatorMixin, generic.UpdateView):
    model = models.Study
    template_name = 'lrex_study/study_archive.html'
    form_class = forms.ArchiveForm
    title = 'Archive the study'

    def form_valid(self, form):
        response = super().form_valid(form)
        self.study.archive()
        return redirect('studies')

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('archive', ''),
        ]


class StudyArchiveDownloadView(StudyObjectMixin, CheckStudyCreatorMixin, generic.DetailView):
    model = models.Study

    def get(self, request, *args, **kwargs):
        filename = '{}_ARCHIVE_{}.zip'.format(self.study.title.replace(' ', '_'), str(now().date()))
        response = HttpResponse(content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        self.study.archive_file(response)
        return response


class StudyRestoreFromArchiveView(StudyMixin, CheckStudyCreatorMixin, SuccessMessageMixin, generic.FormView):
    title = 'Restore study from archive'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.StudyFromArchiveForm
    success_message = 'Study successfully restored.'

    def get(self, request, *args, **kwargs):
        messages.info(self.request, 'Note: Please be patient, restoring a study might take a while.')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        file = form['file'].value()
        self.study.restore_from_archive(file)
        return response

    def get_success_url(self):
        return reverse('study', args=[self.study.slug])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('restore', ''),
        ]


class StudyCreateCopyView(StudyMixin, CheckStudyCreatorMixin, SuccessMessageMixin, generic.FormView):
    title = 'Create a copy of a study'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.StudyCopyForm
    success_message = 'Study successfully created.'

    def get(self, request, *args, **kwargs):
        messages.info(self.request, 'Note: Please be patient, this might take a while.')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        super().form_valid(form)
        title = form['title'].value()
        file = TemporaryFile()
        self.study.archive_file(file)
        study = models.Study.create_from_archive_file(file, self.request.user)
        study.title = title
        study.save()
        return redirect('study', study_slug=study.slug)

    def get_success_url(self):
        return reverse('studies', args=[])

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('copy', ''),
        ]


class StudySettingsNavMixin(StudyNavMixin):
    nav_active = 1

    @property
    def secondary_nav(self):
        return [
            ('link', ('Settings', reverse('study-settings', args=[self.study.slug]))),
            ('link', ('Translations', reverse('study-translate', args=[self.study.slug]))),
        ]


class StudySettingsView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contib_views.LeaveWarningMixin,
    contib_views.ActionsMixin,
    DisableFormIfStudyActiveMixin,
    StudySettingsNavMixin,
    generic.UpdateView,
):
    model = models.Study
    title = 'Study settings'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.StudySettingsForm
    success_message = 'Study settings updated.'

    def get(self, request, *args, **kwargs):
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
            'disable_randomize_question_order': self.study.has_questionnaires,
            'disable_use_blocks': self.study.has_questionnaires,
            'disable_feedback': self.study.is_active,
        })
        return kwargs

    def get_success_url(self):
        if 'save' in self.request.POST:
            return reverse('study-settings', args=[self.object.slug])
        return self.object.get_absolute_url()

    @property
    def actions(self):
        return [
            ('link', 'Delete study', reverse('study-delete', args=[self.study.slug]), self.ACTION_CSS_BUTTON_DANGER),
            ('link', 'Archive study', reverse('study-archive', args=[self.study.slug]), self.ACTION_CSS_BUTTON_PRIMARY)
        ]

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('settings', reverse('study-settings', args=[self.study.slug])),
            ('settings', ''),
        ]


class StudyTranslationsUpdateView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    StudySettingsNavMixin,
    generic.UpdateView,
):
    model = models.Study
    title = 'Translations'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.StudyTranslationsForm
    success_message = 'Translations updated.'
    secondary_nav_active = 1

    def get(self, request, *args, **kwargs):
        msg = 'Note: Translatable elements are not shown, when the respective feature is disabled via a study or ' \
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

    def get_success_url(self):
        if 'save' in self.request.POST:
            return reverse('study-translate', args=[self.object.slug])
        return self.object.get_absolute_url()

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('settings', reverse('study-settings', args=[self.study.slug])),
            ('translations', ''),
        ]


class TasksNavMixin(StudyNavMixin):
    nav_active = 2

    @property
    def secondary_nav(self):
        return [
            ('link', ('Questions', reverse('study-questions', args=[self.study.slug]))),
            ('link', ('Instructions', reverse('study-instructions', args=[self.study.slug]))),
            ('link', ('Intro/outro', reverse('study-intro', args=[self.study.slug]))),
            ('link', ('Demographics', reverse('study-demographics', args=[self.study.slug]))),
        ]




class StudyInstructionsUpdateView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contib_views.LeaveWarningMixin,
    TasksNavMixin,
    DisableFormIfStudyActiveMixin,
    generic.UpdateView,
):
    model = models.Study
    title ='Instructions'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.StudyInstructionsForm
    success_message = 'Instructions saved.'
    secondary_nav_active = 1

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

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('tasks', reverse('study-questions', args=[self.study.slug])),
            ('instructions', ''),
        ]


class StudyIntroUpdateView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contib_views.LeaveWarningMixin,
    TasksNavMixin,
    DisableFormIfStudyActiveMixin,
    generic.UpdateView,
):
    model = models.Study
    title ='Intro/outro'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.StudyIntroForm
    success_message = 'Intro/outro saved.'
    secondary_nav_active = 2

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

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('tasks', reverse('study-questions', args=[self.study.slug])),
            ('intro', ''),
        ]


class QuestionUpdateView(
    StudyMixin,
    CheckStudyCreatorMixin,
    contib_views.LeaveWarningMixin,
    TasksNavMixin,
    DisableFormIfStudyActiveMixin,
    generic.DetailView,
):
    model = models.Study
    title = 'Questions'
    template_name = 'lrex_contrib/crispy_formset_form.html'
    formset = None
    helper = None

    def dispatch(self, *args, **kwargs):
        self.helper = forms.question_formset_helper()
        self.n_questions = self.study.question_set.count()
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.study.has_questionnaires:
            msg = 'Note: To change the "randomize scale" settings you need to ' \
                  '<a href="{}">remove questionnaires</a> first.'.format(reverse('questionnaires', args=[self.study.slug])
            )
            messages.info(request, mark_safe(msg))
        self.formset = forms.question_formset_factory(self.n_questions, 0 if self.n_questions > 0 else 1)(
            queryset=self.study.question_set.all()
        )
        forms.initialize_with_questions(self.formset, self.study.questions)
        forms.question_formset_disable_fields(
            self.formset,
            disable_randomize_scale=self.study.has_questionnaires,
        )
        return super().get(request, *args, **kwargs)

    def _invalidate_materials_items(self):
        for materials in self.study.materials_list:
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
                scale_values_old = list(instance.scalevalue_set.all())
                for j, scale_label in enumerate(form.cleaned_data['scale_labels'].split(',')):
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
            self.n_questions = self.study.question_set.count()
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
                    self.study.question_set.last().delete()
                    if self.study.has_item_questions:
                        self._invalidate_materials_items()
                    self.n_questions -= 1
                self.formset = forms.question_formset_factory(self.n_questions, extra)(
                    queryset=models.Question.objects.filter(study=self.study)
                )
            forms.initialize_with_questions(self.formset, self.study.questions)
            forms.question_formset_disable_fields(
                self.formset,
                disable_randomize_scale=self.study.has_questionnaires,
            )
        return super().get(request, *args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('tasks', reverse('study-questions', args=[self.study.slug])),
            ('questions', ''),
        ]


class SharedWithView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    contib_views.LeaveWarningMixin,
    generic.UpdateView
):
    model = models.Study
    title = 'Share study'
    form_class = forms.SharedWithForm
    template_name = 'lrex_contrib/crispy_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'add_save': True,
        })
        return kwargs

    def get_success_url(self):
        if 'save' in self.request.POST:
            return reverse('study-share', args=[self.object.slug])
        return self.object.get_absolute_url()

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('share', ''),
        ]


class ContactNavMixin(StudyNavMixin):
    nav_active = 5

    @property
    def secondary_nav(self):
        return [
            ('link', ('Contact information', reverse('study-contact', args=[self.study.slug]))),
            ('link', ('Privacy statement', reverse('study-privacy', args=[self.study.slug]))),
        ]


class StudyContactUpdateView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    ContactNavMixin,
    generic.UpdateView,
):
    model = models.Study
    title ='Contact information'
    template_name = 'lrex_contrib/crispy_form.html'
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

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('privacy', reverse('study-contact', args=[self.study.slug])),
            ('contact', ''),
        ]


class StudyPrivacyUpdateView(
    StudyObjectMixin,
    CheckStudyCreatorMixin,
    SuccessMessageMixin,
    contib_views.LeaveWarningMixin,
    DisableFormIfStudyActiveMixin,
    ContactNavMixin,
    generic.UpdateView,
):
    model = models.Study
    title ='Privacy statement'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.StudyPrivacyForm
    success_message = 'Privacy statement saved.'
    secondary_nav_active = 1

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'add_save': True,
        })
        return kwargs

    def get_success_url(self):
        if 'save' in self.request.POST:
            return reverse('study-privacy', args=[self.object.slug])
        return self.object.get_absolute_url()

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('privacy', reverse('study-contact', args=[self.study.slug])),
            ('privacy', ''),
        ]


class StudyResultsCSVDownloadView(StudyObjectMixin, CheckStudyCreatorMixin, generic.DetailView):
    model = models.Study

    def get(self, request, *args, **kwargs):
        filename = '{}_RESULTS_{}.csv'.format(self.study.title.replace(' ', '_'), str(now().date()))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        self.study.results_csv(response)
        return response


class DemographicsUpdateView(
    StudyMixin,
    CheckStudyCreatorMixin,
    contib_views.LeaveWarningMixin,
    TasksNavMixin,
    DisableFormIfStudyActiveMixin,
    generic.DetailView,
):
    model = models.Study
    title = 'Demographics'
    template_name = 'lrex_contrib/crispy_formset_form.html'
    formset = None
    helper = None
    secondary_nav_active = 3

    def dispatch(self, *args, **kwargs):
        self.helper = forms.demographic_formset_helper()
        self.n_fields = self.study.demographicfield_set.count()
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        msg = 'Please, respect the privacy of your participants. Do not collect private data that you do not need.'
        messages.warning(self.request, msg)
        self.formset = forms.demographic_formset_factory(self.n_fields, 0 if self.n_fields > 0 else 1)(
            queryset=self.study.demographicfield_set.all()
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
            self.n_fields = self.study.demographicfield_set.count()
            extra = len(self.formset.forms) - self.n_fields
            if 'submit' in request.POST:
                messages.success(request, 'Demographics saved.')
                return redirect('study', study_slug=self.study.slug)
            elif 'save' in request.POST:
                messages.success(request, 'Demographics saved.')
                self.formset = forms.demographic_formset_factory(self.n_fields, extra)(
                    queryset=self.study.demographicfield_set.all()
                )
            elif 'add' in request.POST:
                self.formset = forms.demographic_formset_factory(self.n_fields, extra + 1)(
                    queryset=self.study.demographicfield_set.all()
                )
            else: # delete last
                if extra > 0:
                    extra -= 1
                elif self.n_fields > 0:
                    self.study.demographicfield_set.last().delete()
                    self.n_fields -= 1
                self.formset = forms.demographic_formset_factory(self.n_fields, extra)(
                    queryset=self.study.demographicfield_set.all()
                )
        return super().get(request, *args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('tasks', reverse('study-questions', args=[self.study.slug])),
            ('demographics', ''),
        ]


