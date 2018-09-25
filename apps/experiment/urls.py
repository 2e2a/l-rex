from django.urls import include, path

from . import views
from apps.item import urls as item_urls

urlpatterns_study = [
    path('create/', views.ExperimentCreateView.as_view(), name='experiment-create'),
    path('results/', views.ExperimentResultListView.as_view(), name='experiment-result-list'),
    path('', views.ExperimentListView.as_view(), name='experiments'),
]

urlpatterns = [
    path('<slug:experiment_slug>/', views.ExperimentDetailView.as_view(), name='experiment'),
    path('<slug:experiment_slug>/update/', views.ExperimentUpdateView.as_view(), name='experiment-update'),
    path('<slug:experiment_slug>/delete/', views.ExperimentDeleteView.as_view(), name='experiment-delete'),
    path('<slug:experiment_slug>/results/', views.ExperimentResultsView.as_view(), name='experiment-results'),
    path('<slug:experiment_slug>/results/csv/', views.ExperimentResultsCSVDownloadView.as_view(), name='experiment-results-csv'),
    path('<slug:experiment_slug>/items/', include(item_urls.urlpatterns_experiment)),
]