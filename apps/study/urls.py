from django.conf.urls import url
from django.conf.urls import include

from . import views

from apps.experiment import urls as experiment_urls
from apps.trial import urls as trial_urls


urlpatterns = [
    url(r'^create/$',
        views.StudyCreateView.as_view(),
        name='study-create'),
    url(r'^update/(?P<slug>[-\w_]+)/$',
        views.StudyUpdateView.as_view(),
        name='study-update'),
    url(r'^delete/(?P<slug>[-\w_]+)/$',
        views.StudyDeleteView.as_view(),
        name='study-delete'),
    url(r'^run/(?P<slug>[-\w_]+)/$',
        views.StudyRunView.as_view(),
        name='study-run'),
    url(r'^responses/(?P<slug>[-\w_]+)/$',
        views.ResponseUpdateView.as_view(),
        name='study-responses'),
    url(r'^(?P<slug>[-\w_]+)/$',
        views.StudyDetailView.as_view(),
        name='study'),
    url(r'^(?P<study_slug>[-\w_]+)/exp/',
        include(experiment_urls)),
    url(r'^(?P<study_slug>[-\w_]+)/trial/',
        include(trial_urls)),
    url(r'',
        views.StudyListView.as_view(),
        name='studies'),
]