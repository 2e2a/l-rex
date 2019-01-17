from django.conf import settings
from django.urls import reverse
from django.views import generic

from . import models


class HomeView(generic.TemplateView):
    template_name = 'lrex_home/home.html'
    title = 'L-Rex: linguistic rating experiments'

    @property
    def breadcrumbs(self):
        return []

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['news_list'] = models.News.objects.all()[:3]
        if self.request.user.is_authenticated:
            data['latest_studies'] = self.request.user.study_set.all()[:2]
        return data


class ImprintView(generic.TemplateView):
    template_name = 'lrex_home/imprint.html'
    title = 'Imprint'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['imprint'] = settings.IMPRINT
        return data

    @property
    def breadcrumbs(self):
        return []


class NewsView(generic.DetailView):
    model = models.News
    title = 'News'

    @property
    def breadcrumbs(self):
        return [
            ('home', reverse('home')),
            ('news', '')
        ]
