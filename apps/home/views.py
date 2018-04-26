from django.conf import settings
from django.views import generic


class HomeView(generic.TemplateView):
    template_name = 'lrex_home/home.html'
    title = 'Linguistic Rating Experiments'


class ImprintView(generic.TemplateView):
    template_name = 'lrex_home/imprint.html'
    title = 'Imprint'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['imprint'] = settings.IMPRINT
        return data
