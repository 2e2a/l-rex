from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'text-item-create/$',
        views.TextItemCreateView.as_view(),
        name='text-item-create'),
    url(r'lists/$',
        views.ListListView.as_view(),
        name='lists'),
]