from django.conf.urls import include
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from apps.home import urls as home_urls
from apps.setup import urls as setup_urls


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^setup/', include(setup_urls)),

    url(r'^accounts/login/',
        auth_views.login,
        {'template_name': 'accounts/login.html'}),
    url(r'^accounts/logout/',
        auth_views.login,
        {'template_name': 'accounts/logged_out.html'}),

    url(r'', include(home_urls)),
]
