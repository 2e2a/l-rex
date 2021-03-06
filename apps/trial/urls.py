from django.urls import path

from . import views

urlpatterns_questionnaires_study = [
    path('', views.QuestionnaireListView.as_view(), name='questionnaires'),
    path('generate/', views.QuestionnaireGenerateView.as_view(), name='questionnaire-generate'),
    path('blocks/', views.QuestionnaireBlockInstructionsUpdateView.as_view(), name='questionnaire-blocks'),
    path('upload/', views.QuestionnaireUploadView.as_view(), name='questionnaire-upload'),
    path('download/', views.QuestionnaireCSVDownloadView.as_view(), name='questionnaire-download'),
    path('delete/', views.QuestionnaireDeleteAllView.as_view(), name='questionnaires-delete'),
]

urlpatterns_questionnaires = [
    path('<slug:questionnaire_slug>/', views.QuestionnaireDetailView.as_view(), name='questionnaire'),
]

urlpatterns_study = [
    path('intro/', views.TrialIntroView.as_view(), name='trial-intro'),
    path('participate/', views.TrialCreateView.as_view(), name='trial-create'),
    path('home/', views.TrialHomeView.as_view(), name='trial-home'),
    path('', views.TrialListView.as_view(), name='trials'),
    path('delete-all/', views.TrialDeleteAllView.as_view(), name='trials-delete'),
    path('participants/download/', views.TrialParticipantsCSVDownloadView.as_view(), name='trials-participants-download'),
    path('participants/delete/', views.TrialDeleteParticipantsView.as_view(), name='trials-participants-delete'),
]

urlpatterns = [
    path('<slug:trial_slug>/', views.TrialDetailView.as_view(), name='trial'),
    path('<slug:trial_slug>/delete/', views.TrialDeleteView.as_view(), name='trial-delete'),
    path('<slug:trial_slug>/demographics/', views.DemographicsCreateView.as_view(), name='trial-demographics'),
    path('<slug:trial_slug>/rating/<int:num>/', views.RatingsCreateView.as_view(), name='ratings-create'),
    path('<slug:trial_slug>/rating/outro/', views.RatingOutroView.as_view(), name='rating-outro'),
    path('<slug:trial_slug>/rating/taken/', views.RatingTakenView.as_view(), name='rating-taken'),
    path('<slug:trial_slug>/rating/instructions/<int:num>/', views.RatingBlockInstructionsView.as_view(),
         name='rating-block-instructions'),
]