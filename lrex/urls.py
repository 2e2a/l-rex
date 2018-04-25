from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import include, path

from apps.home import urls as home_urls
from apps.study import urls as study_urls


urlpatterns = [
    path('study/', include(study_urls)),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('accounts/password_change_done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('admin/', admin.site.urls),
    path('', include(home_urls))
]
