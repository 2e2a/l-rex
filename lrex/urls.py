from django.conf.urls import include
from django.conf.urls import url
from django.contrib import admin

from apps.home import urls as home_urls
from apps.setup import urls as setup_urls


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^setup/', include(setup_urls)),
    url(r'', include(home_urls)),
]
