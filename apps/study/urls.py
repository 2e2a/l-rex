from django.urls import include, path

from . import views

from apps.experiment import urls as experiment_urls
from apps.trial import urls as trial_urls


urlpatterns = [
    path('', views.StudyListView.as_view(), name='studies'),
    path('create/', views.StudyCreateView.as_view(), name='study-create'),
    path('create/from-archive/', views.StudyCreateFromArchiveView.as_view(), name='study-create-archive'),
    path('<slug:study_slug>/', views.StudyDetailView.as_view(), name='study'),
    path('<slug:study_slug>/settings/', views.StudyUpdateView.as_view(), name='study-update'),
    path('<slug:study_slug>/delete/', views.StudyDeleteView.as_view(), name='study-delete'),
    path('<slug:study_slug>/instructions/', views.StudyInstructionsUpdateView.as_view(), name='study-instructions'),
    path('<slug:study_slug>/questions/', views.QuestionUpdateView.as_view(), name='study-questions'),
    path('<slug:study_slug>/share/', views.SharedWithView.as_view(), name='study-share'),
    path('<slug:study_slug>/results/csv/', views.StudyResultsCSVDownloadView.as_view(), name='study-results-csv'),
    path('<slug:study_slug>/archive/', views.StudyArchiveView.as_view(), name='study-archive'),
    path('<slug:study_slug>/archive/download/', views.StudyArchiveDownloadView.as_view(), name='study-archive-download'),
    path('<slug:study_slug>/restore/', views.StudyRestoreFromArchiveView.as_view(), name='study-archive-restore'),
    path('<slug:study_slug>/experiments/', include(experiment_urls.urlpatterns_study)),
    path('<slug:study_slug>/questionnaires/', include(trial_urls.urlpatterns_questionnaires_study)),
    path('<slug:study_slug>/trials/', include(trial_urls.urlpatterns_study)),
]