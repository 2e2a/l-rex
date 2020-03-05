from django.urls import include, path

from . import views
from apps.item import urls as item_urls

urlpatterns_study = [
    path('create/', views.MaterialsCreateView.as_view(), name='materials-create'),
]

urlpatterns = [
    path('<slug:materials_slug>/update/', views.MaterialsSettingsView.as_view(), name='materials-settings'),
    path('<slug:materials_slug>/delete/', views.MaterialsDeleteView.as_view(), name='materials-delete'),
    path('<slug:materials_slug>/results/', views.MaterialsResultsView.as_view(), name='materials-results'),
    path('<slug:materials_slug>/items/', include(item_urls.urlpatterns_materials)),
]