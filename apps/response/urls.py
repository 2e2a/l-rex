from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'settings/binary/create/$',
        views.BinaryResponseSettingsCreateView.as_view(),
        name='binary-response-info-create'),
    url(r'settings/binary/update/(?P<pk>[0-9]+)$',
        views.BinaryResponseSettingsUpdateView.as_view(),
        name='binary-response-info-update'),
    url(r'settings/binary/$',
        views.BinaryResponseSettingsView.as_view(),
        name='binary-response-info'),

    url(r'intro/$',
        views.UserResponseIntroView.as_view(),
        name='user-response-intro'),
    url(r'outro/$',
        views.UserResponseOutroView.as_view(),
        name='user-response-outro'),
    url(r'binary/(?P<num>[0-9]+)/$',
        views.UserBinaryResponseCreateView.as_view(),
        name='user-binary-response'),
]