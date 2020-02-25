from markdownx.utils import markdownify

from django.conf import settings
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.views import generic
from django.views.decorators.csrf import requires_csrf_token

from apps.user import models as user_models
from apps.study import models as study_models

from . import models


@requires_csrf_token
def handler500(request):
    response = render_to_response('lrex_home/error_500.html')
    response.status_code = 500
    return response


class HomeView(generic.ListView):
    model = models.News
    template_name = 'lrex_home/home.html'
    paginate_by = 2

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated and not hasattr(self.request.user, 'userprofile'):
            return redirect('user-profile-create')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'n_users': user_models.UserProfile.objects.all().count(),
            'n_studies': study_models.Study.objects.all().count(),
        })
        return context

class ImprintView(generic.TemplateView):
    template_name = 'lrex_home/imprint.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['contact_rich'] = mark_safe(markdownify(settings.LREX_CONTACT_MD))
        data['privacy_rich'] = mark_safe(markdownify(settings.LREX_PRIVACY_MD))
        return data


class NewsView(generic.DetailView):
    model = models.News

    @property
    def title(self):
        return self.get_object().title

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['news_rich'] = mark_safe(markdownify(self.get_object().text))
        return data
