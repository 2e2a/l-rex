from django.contrib import admin
from django.contrib.auth import urls as auth_urls
from django.urls import include, path

from apps.home import urls as home_urls
from apps.study import urls as study_urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path('study/', include(study_urls)),
    path('accounts/', include(auth_urls)),
    path('', include(home_urls))
]
