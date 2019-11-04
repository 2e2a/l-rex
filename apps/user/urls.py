from django.urls import path

from . import views


urlpatterns = [
    path('profile/create/', views.UserProfileCreateView.as_view(), name='user-profile-create'),
    path('profile/', views.UserProfileUpdateView.as_view(), name='user-profile-update'),
]