from allauth import urls as allauth_urls
from django.conf import settings
from django.conf.urls import handler500
from django.contrib import admin
from django.urls import include, path

from apps.home import urls as home_urls
from apps.home import views as home_views
from apps.item import urls as item_urls
from apps.materials import urls as materials_urls
from apps.study import urls as study_urls
from apps.trial import urls as trial_urls
from apps.user import urls as user_urls

urlpatterns = [
    path('studies/', include(study_urls)),
    path('materials/', include(materials_urls)),
    path('items/', include(item_urls)),
    path('trials/', include(trial_urls.urlpatterns)),
    path('questionnaires/', include(trial_urls.urlpatterns_questionnaires)),
    path('user/', include(user_urls)),
    path('accounts/', include(allauth_urls)),
    path('admin/', admin.site.urls),
    path('markdownx/', include('markdownx.urls')),
    path('', include(home_urls))
]


handler500 = home_views.handler500


if settings.DEV:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
