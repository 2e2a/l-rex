from django.conf.urls import url
from django.conf.urls import include

from apps.results import urls as response_urls
from . import views

urlpatterns = [
    url(r'participate/$',
        views.UserTrialCreateView.as_view(),
        name='user-trial-create'),
    url(r'user-trials/$',
        views.UserTrialListView.as_view(),
        name='user-trials'),
    url(r'user-trial/(?P<slug>[-\w_]+)/delete/',
        views.UserTrialDeleteView.as_view(),
        name='user-trial-delete'),
    url(r'user-trial/(?P<slug>[-\w_]+)/response/',
        include(response_urls)),
    url(r'user-trial/(?P<slug>[-\w_]+)/$',
        views.UserTrialDetailView.as_view(),
        name='user-trial'),
    url(r'questionnaires/$',
        views.QuestionnaireListView.as_view(),
        name='questionnaires'),
]