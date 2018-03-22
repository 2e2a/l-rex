from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import generic

from . import models
from . import forms


class StudyDetailView(LoginRequiredMixin, generic.DetailView):
    model = models.Study
    title = 'Create Study'

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, ''),
        ]

    @property
    def study(self):
        return self.object


class StudyRunView(LoginRequiredMixin, generic.DetailView):
    model = models.Study
    title = 'Run Study'
    template_name = 'lrex_study/study_run.html'

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, ''),
        ]

    @property
    def study(self):
        return self.object


class StudyCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Study
    fields = ['title', 'item_type', 'response_instructions', 'response_question', 'response_legend',
              'start_time', 'end_time', 'password', 'allow_anonymous']
    title = 'Create Study'

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)

class StudyUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = models.Study
    fields = ['title', 'item_type', 'response_instructions', 'response_question', 'response_legend',
              'start_time', 'end_time', 'password', 'allow_anonymous']
    title = 'Edit Study'

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.object.title, reverse('study', args=[self.object.slug])),
            ('settings', ''),
        ]


class StudyDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = models.Study
    title = 'Delete Study'
    message = 'Delete?'

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.object.title, reverse('study', args=[self.object.slug])),
            ('delete', ''),
        ]

    @property
    def cancel_url(self):
        return reverse('studies')

    def get_success_url(self):
        return reverse('studies')


class StudyListView(LoginRequiredMixin, generic.ListView):
    model = models.Study
    title = 'Studies'

    def get_queryset(self):
        return super().get_queryset().filter(creator=self.request.user)

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
        ]


class ResponseUpdateView(LoginRequiredMixin, generic.TemplateView):
    model = models.Study
    title = 'Edit Reponse'
    template_name = 'lrex_study/study_responses.html'

    formset = None
    helper = forms.response_formset_helper

    def dispatch(self, *args, **kwargs):
        study_slug = self.kwargs['slug']
        self.study = models.Study.objects.get(slug=study_slug)
        self.formset = forms.responseformset_factory(
            queryset=models.Response.objects.filter(study=self.study)
        )
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.formset = forms.responseformset_factory(request.POST, request.FILES)
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
            self.formset = forms.responseformset_factory(
                queryset=models.Response.objects.filter(study=self.study)
            )
        return super().get(request, *args, **kwargs)


    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('responses', ''),
        ]
