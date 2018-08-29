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
    path('<slug:slug>/questions/', views.QuestionListView.as_view(), name='study-questions'),
    path('<slug:slug>/questions/create/', views.QuestionCreateView.as_view(), name='study-question-create'),
    path('<slug:slug>/questions/update/<int:pk>/', views.QuestionUpdateView.as_view(), name='study-question-update'),
    path('<slug:slug>/questions/delete/<int:pk>/', views.QuestionDeleteView.as_view(), name='study-question-delete'),
    path('<slug:slug>/questions/scale/<int:pk>/', views.ScaleUpdateView.as_view(), name='study-question-scale'),
    path('<slug:slug>/questions/<int:pk>/', views.QuestionDetailView.as_view(), name='study-question'),
    path('<slug:study_slug>/exp/', include(experiment_urls)),
    path('<slug:study_slug>/trial/', include(trial_urls)),
    path('', views.StudyListView.as_view(), name='studies'),
]