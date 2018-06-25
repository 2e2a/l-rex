from django.urls import path

from . import views

urlpatterns = [
    path('questionnaires/', views.QuestionnaireListView.as_view(), name='questionnaires'),
    path('trials/', views.TrialListView.as_view(), name='trials'),
    path('delete/<slug:slug>/', views.TrialDeleteView.as_view(), name='trial-delete'),
    path('participate/', views.TrialCreateView.as_view(), name='trial-create'),
    path('<slug:slug>/rating/outro/', views.RatingOutroView.as_view(), name='rating-outro'),
    path('<slug:slug>/rating/taken/', views.RatingTakenView.as_view(), name='rating-taken'),
    path('<slug:slug>/rating/<int:num>/', views.RatingCreateView.as_view(), name='rating-create'),
    path('<slug:slug>/', views.TrialDetailView.as_view(), name='trial'),
]