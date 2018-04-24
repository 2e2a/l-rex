from django.urls import include, path

from apps.item import urls as item_urls
from . import views

urlpatterns = [
    path('<slug:slug>/item/', include(item_urls)),
    path('create/', views.ExperimentCreateView.as_view(), name='experiment-create'),
    path('update/<slug:slug>/', views.ExperimentUpdateView.as_view(), name='experiment-update'),
    path('delete/<slug:slug>/', views.ExperimentDeleteView.as_view(), name='experiment-delete'),
    path('results/', views.ExperimentResultListView.as_view(), name='experiment-result-list'),
    path('results/<slug:slug>/', views.ExperimentResultsView.as_view(), name='experiment-results'),
    path('results/<slug:slug>/csv/', views.ExperimentResultsCSVDownloadView.as_view(), name='experiment-results-csv'),
    path('<slug:slug>/', views.ExperimentDetailView.as_view(), name='experiment'),
    path('', views.ExperimentListView.as_view(), name='experiments'),
]