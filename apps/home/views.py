from markdownx.utils import markdownify

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views import generic
from django.views.decorators.csrf import requires_csrf_token

from apps.user import models as user_models
from apps.study import models as study_models

from . import models
from . import forms


@requires_csrf_token
def handler500(request):
    response = render(request, 'lrex_home/error_500.html')
    response.status_code = 500
    return response


class HomeView(generic.ListView):
    model = models.News
    template_name = 'lrex_home/home.html'
    paginate_by = 2

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated and not hasattr(self.request.user, 'userprofile'):
            return redirect('user-account-create')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'n_users': user_models.UserProfile.objects.all().count(),
            'n_studies': study_models.Study.objects.all().count(),
        })
        return context


class ContactView(generic.TemplateView):
    template_name = 'lrex_home/contact.html'
    title = 'Contact'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['contact_rich'] = mark_safe(markdownify(settings.LREX_CONTACT_MD))
        return data


class PrivacyView(generic.TemplateView):
    template_name = 'lrex_home/privacy.html'
    title = 'Privacy statement'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['privacy_rich'] = mark_safe(markdownify(settings.LREX_PRIVACY_MD))
        return data


class HelpView(generic.TemplateView):
    template_name = 'lrex_home/help.html'
    title = 'Help'


class AboutView(generic.TemplateView):
    template_name = 'lrex_home/about.html'
    title = 'About'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'version': settings.LREX_VERSION,
            'year': now().year,
        })
        return context


class DemoView(generic.TemplateView):
    template_name = 'lrex_home/demo.html'
    title = 'Demo studies'


class NewsView(generic.DetailView):
    model = models.News

    @property
    def title(self):
        return self.get_object().title

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['news_rich'] = mark_safe(markdownify(self.get_object().text))
        return data


class DonateView(generic.TemplateView):
    template_name = 'lrex_home/donate.html'
    title = 'Support us'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data.update({
            'study': self.request.GET.get('study'),
            'recipient': settings.LREX_RECIPIENT,
            'iban': settings.LREX_IBAN,
            'bic': settings.LREX_BIC,
        })
        return data

class InvoiceRequestView(LoginRequiredMixin, generic.FormView):
    template_name = 'lrex_home/invoice_form.html'
    form_class = forms.InvoiceRequestForm
    title = 'Request an invoice'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'user': self.request.user,
            'study': self.request.GET.get('study'),
        })
        return kwargs

    def get_success_url(self):
        return reverse('invoice-requested')

    def form_valid(self, form):
        study_pk = form['study'].value()
        if study_pk:
            study = study_models.Study.objects.filter(pk=study_pk).first()
            if study:
                study.has_invoice = True
                study.save()
        form.send_mail()
        return super().form_valid(form)


class InvoiceRequestedView(generic.TemplateView):
    template_name = 'lrex_home/invoice_done.html'
    title = 'Invoice request sent'
