from django.urls import path

from . import views


urlpatterns = [
    path('account/create/', views.UserAccountCreateView.as_view(), name='user-account-create'),
    path('account/delete/', views.UserAccountDeleteView.as_view(), name='user-account-delete'),
    path('account/', views.UserAccountUpdateView.as_view(), name='user-account-update'),
]