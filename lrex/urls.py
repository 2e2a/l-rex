from django.conf.urls import include
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from apps.home import urls as home_urls
from apps.study import urls as study_urls


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^study/', include(study_urls)),

    url(r'^accounts/login/',
        auth_views.login,
        {'template_name': 'accounts/login.html'},
        name='login'),
    url(r'^accounts/logout/',
        auth_views.logout,
        {'template_name': 'accounts/logged_out.html'},
        name='logout'),

    url(r'', include(home_urls)),
]
