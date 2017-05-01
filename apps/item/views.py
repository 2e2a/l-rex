from django.shortcuts import redirect
from django.views import generic

from apps.experiment import models as experiment_models

from . import models


class TextItemCreateView(generic.CreateView):
    model = models.TextItem
    fields = ['number', 'condition', 'text']

    def dispatch(self, *args, **kwargs):
        experiment_slug = self.kwargs['slug']
        self.experiment = experiment_models.Experiment.objects.get(slug=experiment_slug)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.experiment = self.experiment
        return super().form_valid(form)


class ListListView(generic.ListView):
    model = models.List

    def dispatch(self, *args, **kwargs):
        experiment_slug = self.kwargs['slug']
        self.experiment = experiment_models.Experiment.objects.get(slug=experiment_slug)
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'generate_lists':
            self.experiment.compute_lists()
        return redirect('lists',setup_slug=self.experiment.setup.slug, slug=self.experiment.slug)


    def get_queryset(self):
        return models.List.objects.filter(experiment=self.experiment)
