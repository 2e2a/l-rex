from django.views import generic

from apps.setup import models as setup_models

from . import models


class TrialListView(generic.ListView):
    model = models.Trial

    def dispatch(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        self.setup = setup_models.Setup.objects.get(slug=setup_slug)
        self.setup.generate_trials()
        return super().dispatch(*args, **kwargs)


class UserTrialListView(generic.ListView):
    model = models.UserTrial

    def dispatch(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        self.setup = setup_models.Setup.objects.get(slug=setup_slug)
        return super().dispatch(*args, **kwargs)


class UserTrialCreateView(generic.CreateView):
    model = models.UserTrial
    fields = ['participant']

    def dispatch(self, *args, **kwargs):
        setup_slug = self.kwargs['setup_slug']
        self.setup = setup_models.Setup.objects.get(slug=setup_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.setup = self.setup
        form.instance.generate()
        return super().form_valid(form)

class UserTrialDetailView(generic.DetailView):
    model = models.UserTrial
