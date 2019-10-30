from django.urls import include, path

from . import views
from apps.item import urls as item_urls

urlpatterns_study = [
    path('create/', views.MaterialsCreateView.as_view(), name='materials-create'),
    path('results/', views.MaterialsResultListView.as_view(), name='materials-result-list'),
    path('', views.MaterialsListView.as_view(), name='materials-list'),
]

urlpatterns = [
    path('<slug:materials_slug>/', views.MaterialsDetailView.as_view(), name='materials'),
    path('<slug:materials_slug>/update/', views.MaterialsUpdateView.as_view(), name='materials-update'),
    path('<slug:materials_slug>/delete/', views.MaterialsDeleteView.as_view(), name='materials-delete'),
    path('<slug:materials_slug>/results/', views.MaterialsResultsView.as_view(), name='materials-results'),
    path('<slug:materials_slug>/results/csv/', views.MaterialsResultsCSVDownloadView.as_view(), name='materials-results-csv'),
    path('<slug:materials_slug>/items/', include(item_urls.urlpatterns_materials)),
]