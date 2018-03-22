from django.conf.urls import url
from django.conf.urls import include

from apps.results import urls as response_urls
from . import views

urlpatterns = [
    url(r'participate/$',
        views.TrialCreateView.as_view(),
        name='trial-create'),
    url(r'trials/$',
        views.TrialListView.as_view(),
        name='trials'),
    url(r'trial/(?P<slug>[-\w_]+)/delete/',
        views.TrialDeleteView.as_view(),
        name='trial-delete'),
    url(r'trial/(?P<slug>[-\w_]+)/response/',
        include(response_urls)),
    url(r'trial/(?P<slug>[-\w_]+)/$',
        views.TrialDetailView.as_view(),
        name='trial'),
    url(r'questionnaires/$',
        views.QuestionnaireListView.as_view(),
        name='questionnaires'),
]