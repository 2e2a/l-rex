from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views import generic

from apps.contrib import views as contib_views

from . import models
from . import forms


def progress_success_message(progress):
    return 'Success: {}'.format(models.Study.progress_description(progress))


class NextStepsMixin:
    study = None
    experiment = None

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        next_steps = self.study.next_steps()
        for next_step in next_steps:
            description, url = next_step
            message = 'Next: {}'.format(description)
            if url and self.request.path != url:
                message = message + ' (<a href="{}">here</a>)'.format(url)
            messages.info(request, mark_safe(message))
        return response


class StudyDetailView(LoginRequiredMixin, NextStepsMixin, generic.DetailView):
    model = models.Study
    title = 'Edit study'

    @property
    def study(self):
        return self.object

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, ''),
        ]


class StudyRunView(LoginRequiredMixin, NextStepsMixin, generic.DetailView):
    model = models.Study
    title = 'Run study'
    template_name = 'lrex_study/study_run.html'

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, ''),
        ]

    @property
    def study(self):
        return self.get_object()


class StudyCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Study
    title = 'Create study'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.StudyForm
    success_message = 'Study successfully created.'

    def form_valid(self, form):
        form.instance.creator = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, progress_success_message(form.instance.progress))
        return response


class StudyUpdateView(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = models.Study
    title = 'Edit study'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.StudyForm
    success_message = 'Study successfully updated.'

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.object.title, reverse('study', args=[self.object.slug])),
            ('settings', ''),
        ]


class StudyDeleteView(LoginRequiredMixin, contib_views.DefaultDeleteView):
    model = models.Study

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.object.title, reverse('study', args=[self.object.slug])),
            ('delete', ''),
        ]

    def get_success_url(self):
        return reverse('studies')


class StudyListView(LoginRequiredMixin, generic.ListView):
    model = models.Study
    title = 'Studies'

    def get_queryset(self):
        return super().get_queryset().filter(creator=self.request.user)

    def post(self, request, *args, **kwargs):
        study_slug = request.POST.get('publish', None)
        if study_slug:
            study = models.Study.objects.get(slug=study_slug)
            study.is_published = True
            study.set_progress(study.PROGRESS_STD_PUBLISHED)
            messages.success(request, progress_success_message(study.progress))
            study.save()
        study_slug = request.POST.get('unpublish', None)
        if study_slug:
            study = models.Study.objects.get(slug=study_slug)
            study.is_published = False
            study.set_progress(study.PROGRESS_STD_QUESTIONNARES_GENERATED)
            messages.success(request, 'Study unpublished.')
        return redirect('studies')

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
        ]


class QuestionUpdateView(LoginRequiredMixin, NextStepsMixin, generic.TemplateView):
    title = 'Questions'
    template_name = 'lrex_contrib/crispy_formset_form.html'
    formset = None
    helper = forms.question_formset_helper

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['slug']
        self.study = models.Study.objects.get(slug=study_slug)
        self.n_questions = self.study.question_set.count()
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.formset = forms.question_formset_factory(self.n_questions, 0 if self.n_questions > 0 else 1)(
            queryset=models.Question.objects.filter(study=self.study)
        )
        forms.initialize_with_questions(self.formset, self.study.question_set.all())
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.formset = forms.question_formset_factory(self.n_questions)(request.POST, request.FILES)
        extra = len(self.formset.forms) - self.n_questions
        if 'submit' in request.POST:
            if self.formset.is_valid():
                instances = self.formset.save(commit=False)
                for instance, form in zip(instances, self.formset):
                    instance.study = self.study
                    instance.scalevalue_set.all().delete()
                    for scale_label in form.cleaned_data['scale_labels'].split(','):
                        if scale_label:
                            models.ScaleValue.objects.create(
                                question=instance,
                                label=scale_label,
                            )
            self.study.set_progress(self.study.PROGRESS_STD_QUESTION_CREATED)
            messages.success(request, progress_success_message(self.study.progress))
        elif 'add' in request.POST:
            self.formset = forms.question_formset_factory(self.n_questions, extra + 1)(
                queryset=models.Question.objects.filter(study=self.study)
            )
        else: # delete last
            if extra > 0:
                extra -= 1
            elif self.n_questions > 0:
                self.study.question_set.last().delete()
                self.n_questions -= 1
            self.formset = forms.question_formset_factory(self.n_questions, extra)(
                queryset=models.Question.objects.filter(study=self.study)
            )
        forms.initialize_with_questions(self.formset, self.study.question_set.all())
        return super().get(request, *args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('questions', ''),
        ]
