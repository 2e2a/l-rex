from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^create/$',
        views.SetupCreateView.as_view(),
        name='setup-create'),
    url(r'^(?P<slug>[-\w_]+)/$',
        views.SetupDetailView.as_view(),
        name='setup'),
    url(r'^(?P<setup_slug>[-\w_]+)/exp/(?P<slug>[-\w_]+)/$',
        views.ExperimentDetailView.as_view(),
        name='experiment'),
]