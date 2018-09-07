from django.urls import include, path

from . import views

from apps.experiment import urls as experiment_urls
from apps.trial import urls as trial_urls


urlpatterns = [
    path('create/', views.StudyCreateView.as_view(), name='study-create'),
    path('update/<slug:slug>/', views.StudyUpdateView.as_view(), name='study-update'),
    path('delete/<slug:slug>/', views.StudyDeleteView.as_view(), name='study-delete'),
    path('run/<slug:slug>/', views.StudyRunView.as_view(), name='study-run'),
    path('<slug:slug>/', views.StudyDetailView.as_view(), name='study'),
    path('<slug:slug>/questions/', views.QuestionUpdateView.as_view(), name='study-questions'),
    path('<slug:study_slug>/exp/', include(experiment_urls)),
    path('<slug:study_slug>/trial/', include(trial_urls)),
    path('', views.StudyListView.as_view(), name='studies'),
]