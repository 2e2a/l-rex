from django.views import generic


class HomeView(generic.TemplateView):
    template_name = 'lrex_home/home.html'
    title = 'Linguistic Rating Experiments'
