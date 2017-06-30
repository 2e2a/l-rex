from django.conf.urls import url
from django.conf.urls import include

from . import views

from apps.experiment import urls as experiment_urls
from apps.responseinfo import urls as responseinfo_url
from apps.trial import urls as trial_urls


urlpatterns = [
    url(r'^create/$',
        views.SetupCreateView.as_view(),
        name='setup-create'),
    url(r'^update/(?P<slug>[-\w_]+)/$',
        views.SetupUpdateView.as_view(),
        name='setup-update'),
    url(r'^delete/(?P<slug>[-\w_]+)/$',
        views.SetupDeleteView.as_view(),
        name='setup-delete'),
    url(r'^(?P<slug>[-\w_]+)/$',
        views.SetupDetailView.as_view(),
        name='setup'),
    url(r'^(?P<setup_slug>[-\w_]+)/exp/',
        include(experiment_urls)),
    url(r'^(?P<setup_slug>[-\w_]+)/trial/',
        include(trial_urls)),
    url(r'^(?P<setup_slug>[-\w_]+)/responseinfo/',
        include(responseinfo_url)),
    url(r'',
        views.SetupListView.as_view(),
        name='setups'),
]