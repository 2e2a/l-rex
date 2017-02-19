from django.conf.urls import include
from django.conf.urls import url
from django.contrib import admin

from apps.experiment import urls as experiment_urls

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^exp/', include(experiment_urls)),
]
