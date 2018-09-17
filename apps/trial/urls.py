from django.urls import path

from . import views

urlpatterns = [
    path('questionnaires/', views.QuestionnaireListView.as_view(), name='questionnaires'),
    path('questionnaires/generate/', views.QuestionnaireGenerateView.as_view(), name='questionnaire-generate'),
    path('trials/', views.TrialListView.as_view(), name='trials'),
    path('delete/<slug:slug>/', views.TrialDeleteView.as_view(), name='trial-delete'),
    path('participate/', views.TrialCreateView.as_view(), name='trial-create'),
    path('<slug:slug>/rating/outro/', views.RatingOutroView.as_view(), name='rating-outro'),
    path('<slug:slug>/rating/taken/', views.RatingTakenView.as_view(), name='rating-taken'),
    path('<slug:slug>/rating/<int:num>/', views.RatingCreateView.as_view(), name='rating-create'),
    path('<slug:slug>/ratings/<int:num>/', views.RatingsCreateView.as_view(), name='ratings-create'),
    path('<slug:slug>/rating/instuctions/<int:num>/', views.RatingBlockInstructionsView.as_view(),
         name='rating-block-instructions'),
    path('<slug:slug>/', views.TrialDetailView.as_view(), name='trial'),
]