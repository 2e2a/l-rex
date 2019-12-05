from markdownx.utils import markdownify

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views import generic

from . import models


class HomeView(generic.ListView):
    model = models.News
    template_name = 'lrex_home/home.html'
    title = 'Linguistic rating experiments'
    paginate_by = 2

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated and not hasattr(self.request.user, 'userprofile'):
            return redirect('user-profile-create')
        return super().get(request, *args, **kwargs)

    @property
    def breadcrumbs(self):
        return []


class ImprintView(generic.TemplateView):
    template_name = 'lrex_home/imprint.html'
    title = 'Imprint'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['contact_rich'] = mark_safe(markdownify(settings.LREX_CONTACT_MD))
        data['privacy_rich'] = mark_safe(markdownify(settings.LREX_PRIVACY_MD))
        return data

    @property
    def breadcrumbs(self):
        return []


class NewsView(generic.DetailView):
    model = models.News

    @property
    def title(self):
        return self.get_object().title

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['news_rich'] = mark_safe(markdownify(self.get_object().text))
        return data

    @property
    def breadcrumbs(self):
        return [
            ('home', reverse('home')),
            ('news', '')
        ]
