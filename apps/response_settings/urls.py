from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'binary/create/$',
        views.BinaryResponseSettingsCreateView.as_view(),
        name='binary-response-settings-create'),
    url(r'binary/update/(?P<pk>[0-9]+)$',
        views.BinaryResponseSettingsUpdateView.as_view(),
        name='binary-response-settings-update'),
    url(r'binary/$',
        views.BinaryResponseSettingsView.as_view(),
        name='binary-response-settings'),

]