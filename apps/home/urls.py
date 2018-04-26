from django.urls import path

from . import views


urlpatterns = [
    path('imprint/', views.ImprintView.as_view(), name='imprint'),
    path('', views.HomeView.as_view(), name='home'),
]