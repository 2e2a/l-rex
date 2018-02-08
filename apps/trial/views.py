from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import generic

from apps.setup import models as setup_models

from . import models


class TrialListView(LoginRequiredMixin, generic.ListView):
    model = models.Trial
    title = 'Trial List'

    def dispatch(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        self.setup = setup_models.Setup.objects.get(slug=setup_slug)
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'generate_trials':
            self.setup.generate_trials()
        return redirect('trials',setup_slug=self.setup.slug)


class UserTrialListView(LoginRequiredMixin, generic.ListView):
    model = models.UserTrial
    title = 'User Trial List'

    def dispatch(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        self.setup = setup_models.Setup.objects.get(slug=setup_slug)
        return super().dispatch(*args, **kwargs)


class UserTrialCreateView(LoginRequiredMixin, generic.CreateView):
    model = models.UserTrial
    fields = ['participant']
    title = 'Create User Trial'

    def dispatch(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        self.setup = setup_models.Setup.objects.get(slug=setup_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.setup = self.setup
        form.instance.init()
        response = super().form_valid(form)
        form.instance.generate_items()
        return response

class UserTrialDetailView(LoginRequiredMixin, generic.DetailView):
    model = models.UserTrial
    title = 'User Trial Overview'
