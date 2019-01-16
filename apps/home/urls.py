from django.urls import path

from . import views


urlpatterns = [
    path('imprint/', views.ImprintView.as_view(), name='imprint'),
    path('news/<slug:slug>/', views.NewsView.as_view(), name='news'),
    path('', views.HomeView.as_view(), name='home'),
]