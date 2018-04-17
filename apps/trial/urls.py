from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^questionnaires/$',
        views.QuestionnaireListView.as_view(),
        name='questionnaires'),
    url(r'^participate/$',
        views.TrialCreateView.as_view(),
        name='trial-create'),
    url(r'^trials/$',
        views.TrialListView.as_view(),
        name='trials'),
    url(r'^delete/(?P<slug>[-\w_]+)/$',
        views.TrialDeleteView.as_view(),
        name='trial-delete'),
    url(r'^(?P<slug>[-\w_]+)/rating/intro/$',
        views.RatingIntroView.as_view(),
        name='rating-intro'),
    url(r'^(?P<slug>[-\w_]+)/rating/outro/$',
        views.RatingOutroView.as_view(),
        name='rating-outro'),
    url(r'^(?P<slug>[-\w_]+)/rating/taken/$',
        views.RatingTakenView.as_view(),
        name='rating-taken'),
    url(r'^(?P<slug>[-\w_]+)/rating/(?P<num>[0-9]+)/$',
        views.RatingCreateView.as_view(),
        name='rating-create'),
    url(r'^(?P<slug>[-\w_]+)/$',
        views.TrialDetailView.as_view(),
        name='trial'),
]