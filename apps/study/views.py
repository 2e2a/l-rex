from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views import generic

from apps.trial import models as trial_models
from apps.contrib import views as contib_views

from . import models
from . import forms


class WarnUserIfStudyActiveMixin:

    def get(self, request, *args, **kwargs):
        if self.study.is_active:
            if hasattr(self, 'form_valid') or hasattr(self, 'helper'):
                msg = 'Note: Form is disabled.'
            else:
                msg = 'Note: Actions are disabled.'
            msg = msg + 'You cannot change an active study. Please <a href="{}">unpublish</a> ' \
                        'the study and save and <a href="{}">remove the results</a> first.'\
                        .format(
                            reverse('study', args=[self.study.slug]),
                            reverse('trials', args=[self.study.slug])
                        )
            messages.info(request, mark_safe(msg))
        return  super().get(request, *args, **kwargs)


class DisableFormIfStudyActiveMixin(WarnUserIfStudyActiveMixin):

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['disable_actions'] = self.study.is_active
        return data

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        if self.study.is_active:
            for helper_input in form.helper.inputs:
                helper_input.field_classes += '  disabled'
                helper_input.flat_attrs += '  disabled=True'
        return form

    def get(self, request, *args, **kwargs):
        if self.study.is_active:
            if hasattr(self, 'helper'):
                for helper_input in self.helper.inputs:
                    helper_input.field_classes += '  disabled'
                    helper_input.flat_attrs += '  disabled=True'
        return  super().get(request, *args, **kwargs)


class NextStepsMixin:

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        next_steps = self.study.next_steps()
        for description, url in next_steps:
            message = 'Next: {}'.format(description)
            if url and self.request.path != url:
                message = message + ' (<a href="{}">here</a>)'.format(url)
            messages.info(request, mark_safe(message))
        return response


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


class StudyListView(LoginRequiredMixin, generic.ListView):
    model = models.Study
    title = 'Studies'
    paginate_by = 16

    def get_queryset(self):
        return super().get_queryset().filter(
            Q(creator=self.request.user) |
            Q(shared_with__contains=self.request.user.username)
        )

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
        ]


class StudyCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Study
    title = 'Create study'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.StudyForm
    success_message = 'Study successfully created.'

    def form_valid(self, form):
        form.instance.creator = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Study successfully created.')
        return response


class StudyDetailView(StudyObjectMixin, CheckStudyCreatorMixin, NextStepsMixin, generic.DetailView):
    model = models.Study

    @property
    def title(self):
        return self.study.title

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
        data['trial_count'] = self.study.trial_count
        data['experiments_ready'] = []
        data['experiments_draft'] = []
        for experiment in self.study.experiments:
            data['experiments_ready' if experiment.is_complete else 'experiments_draft'].append(experiment)
        return data

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, ''),
        ]


class StudyUpdateView(StudyObjectMixin, CheckStudyCreatorMixin, SuccessMessageMixin, generic.UpdateView):
    model = models.Study
    title = 'Edit study'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.StudyForm
    success_message = 'Study successfully updated.'

    def get(self, request, *args, **kwargs):
        if self.study.is_active:
            msg = 'Note: You cannot change the title of an active study. Please <a href="{}">unpublish</a> ' \
                  'the study and save and <a href="{}">remove the results</a> first'.format(
                    reverse('study', args=[self.study.slug]),
                    reverse('trials', args=[self.study.slug]))
            messages.info(request, mark_safe(msg))
        if self.study.has_items:
            msg = 'Note: To change the "item type" setting you would need to remove old items first' \
                  ' (<a href="{}">here</a>).'.format(reverse('experiments', args=[self.study.slug]))
            messages.info(request, mark_safe(msg))
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['disable_title'] =  self.study.is_active
        kwargs['disable_itemtype'] = self.study.has_items
        return kwargs

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('settings', ''),
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


class StudyInstructionsUpdateView(StudyObjectMixin, CheckStudyCreatorMixin, SuccessMessageMixin,
                                  DisableFormIfStudyActiveMixin, generic.UpdateView):
    model = models.Study
    title ='Edit study instructions'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.StudyInstructionsForm
    success_message = 'Instructions saved.'

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('instructions', ''),
        ]


class QuestionUpdateView(StudyMixin, CheckStudyCreatorMixin, DisableFormIfStudyActiveMixin, generic.DetailView):
    model = models.Study
    title = 'Questions'
    template_name = 'lrex_contrib/crispy_formset_form.html'
    formset = None
    helper = forms.question_formset_helper

    def dispatch(self, *args, **kwargs):
        self.n_questions = self.study.question_set.count()
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.formset = forms.question_formset_factory(self.n_questions, 0 if self.n_questions > 0 else 1)(
            queryset=models.Question.objects.filter(study=self.study)
        )
        forms.initialize_with_questions(self.formset, self.study.questions)
        return super().get(request, *args, **kwargs)

    def _invalidate_experiment_items(self):
        for experiment in self.study.experiments:
            experiment.items_validated = False
            experiment.save()

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
                    self._invalidate_experiment_items()
                for scale_value in scale_values_old:
                    scale_value.delete()
            extra = len(self.formset.forms) - self.n_questions
            if 'submit' in request.POST:
                messages.success(request, 'Questions saved.')
                return redirect('study', study_slug=self.study.slug)
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
                        self._invalidate_experiment_items()
                    self.n_questions -= 1
                self.formset = forms.question_formset_factory(self.n_questions, extra)(
                    queryset=models.Question.objects.filter(study=self.study)
                )
            forms.initialize_with_questions(self.formset, self.study.questions)
        return super().get(request, *args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('questions', ''),
        ]


class SharedWithView(StudyObjectMixin, CheckStudyCreatorMixin, NextStepsMixin, generic.UpdateView):
    model = models.Study
    title = 'Share study'
    form_class = forms.SharedWithForm
    template_name = 'lrex_contrib/crispy_form.html'

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('share', ''),
        ]

    def get_success_url(self):
        return reverse('study', args=[self.study.slug])


class StudyResultsCSVDownloadView(StudyObjectMixin, CheckStudyCreatorMixin, generic.DetailView):
    model = models.Study

    def get(self, request, *args, **kwargs):
        filename = self.study.slug + '.csv'
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
        self.study.results_csv(response,  )
        return response
