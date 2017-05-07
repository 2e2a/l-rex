from django.conf.urls import url

from . import views

urlpatterns = [
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