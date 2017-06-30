from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'binary/create/$',
        views.BinaryResponseInfoCreateView.as_view(),
        name='binary-response-info-create'),
    url(r'binary/update/(?P<pk>[0-9]+)$',
        views.BinaryResponseInfoUpdateView.as_view(),
        name='binary-response-info-update'),
    url(r'binary/$',
        views.BinaryResponseInfoDetailView.as_view(),
        name='binary-response-info'),
]