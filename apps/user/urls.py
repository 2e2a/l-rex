from django.urls import path

from . import views


urlpatterns = [
    path('create/', views.UserAccountCreateView.as_view(), name='user-account-create'),
    path('delete/', views.UserAccountDeleteView.as_view(), name='user-account-delete'),
    path('settings/', views.UserAccountUpdateView.as_view(), name='user-account-update'),
    path('email/', views.UserEmailChangeView.as_view(), name='user-email-change'),
]