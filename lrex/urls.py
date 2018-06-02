from allauth import urls as allauth_urls
from django.contrib import admin
from django.urls import include, path

from apps.home import urls as home_urls
from apps.study import urls as study_urls


urlpatterns = [
    path('study/', include(study_urls)),
    path('accounts/', include(allauth_urls)),
    path('admin/', admin.site.urls),
    path('', include(home_urls))
]
