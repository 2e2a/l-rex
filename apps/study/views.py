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


class ScaleUpdateView(LoginRequiredMixin, NextStepsMixin, generic.TemplateView):
    model = models.Study
    title = 'Edit rating scale'
    template_name = 'lrex_study/study_scale.html'

    formset = None
    helper = forms.scale_formset_helper

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['slug']
        self.study = models.Study.objects.get(slug=study_slug)
        self.formset = forms.scaleformset_factory()(
            queryset=models.ScaleValue.objects.filter(study=self.study)
        )
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.formset = forms.scaleformset_factory()(request.POST, request.FILES)
        if self.formset.is_valid():
            instances = self.formset.save(commit=False)
            for instance in instances:
                instance.number = 0
                instance.study = self.study
                instance.save()
            i = 1
            for form in self.formset.forms:
                if form.instance.id:
                    if form.cleaned_data['delete']:
                        form.instance.delete()
                    else:
                        form.instance.number = i
                        form.instance.save()
                        i = i + 1

            if 'add' in request.POST:
                extra = 1
            else:
                extra = 0
                if self.study.experiment_set.exists():
                    self.study.set_progress(self.study.PROGRESS_STD_EXP_CREATED)
                else:
                    self.study.set_progress(self.study.PROGRESS_STD_SCALE_CONFIGURED)
                    messages.success(request, progress_success_message(self.study.progress))


            self.formset = forms.scaleformset_factory(extra)(
                queryset=models.ScaleValue.objects.filter(study=self.study)
            )

        return super().get(request, *args, **kwargs)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('scale', ''),
        ]
