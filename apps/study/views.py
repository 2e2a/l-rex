from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import generic

from . import models


class StudyDetailView(LoginRequiredMixin, generic.DetailView):
    model = models.Study
    title = 'Create Study'

    @property
    def breadcrumbs(self):
        return [
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
            (self.study.title, ''),
        ]

    @property
    def study(self):
        return self.object


class StudyCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.Study
    fields = ['title', 'item_type']
    title = 'Create Study'

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)

class StudyUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = models.Study
    fields = ['title', 'item_type']
    title = 'Edit Study'

    @property
    def breadcrumbs(self):
        return [
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
