from django.urls import path

from . import views

urlpatterns_study_questionnaires = [
    path('', views.QuestionnaireListView.as_view(), name='questionnaires'),
    path('generate/', views.QuestionnaireGenerateView.as_view(), name='questionnaire-generate'),
    path('blocks/', views.QuestionnaireBlockUpdateView.as_view(), name='questionnaire-blocks'),
]

urlpatterns_study = [
    path('', views.TrialListView.as_view(), name='trials'),
    path('participate/', views.TrialCreateView.as_view(), name='trial-create'),
]

urlpatterns = [
    path('<slug:trial_slug>/', views.TrialDetailView.as_view(), name='trial'),
    path('<slug:trial_slug>/delete/', views.TrialDeleteView.as_view(), name='trial-delete'),
    path('<slug:trial_slug>/rating/<int:num>/', views.RatingCreateView.as_view(), name='rating-create'),
    path('<slug:trial_slug>/ratings/<int:num>/', views.RatingsCreateView.as_view(), name='ratings-create'),
    path('<slug:trial_slug>/rating/outro/', views.RatingOutroView.as_view(), name='rating-outro'),
    path('<slug:trial_slug>/rating/taken/', views.RatingTakenView.as_view(), name='rating-taken'),
    path('<slug:trial_slug>/rating/instuctions/<int:num>/', views.RatingBlockInstructionsView.as_view(),
         name='rating-block-instructions'),
]