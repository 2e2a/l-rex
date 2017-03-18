from django.conf.urls import url
from django.conf.urls import include

from . import views

from apps.experiment import urls as experiment_urls

urlpatterns = [
    url(r'^create/$',
        views.SetupCreateView.as_view(),
        name='setup-create'),
    url(r'^(?P<slug>[-\w_]+)/$',
        views.SetupDetailView.as_view(),
        name='setup'),
    url(r'^(?P<setup_slug>[-\w_]+)/exp/',
        include(experiment_urls)),
]