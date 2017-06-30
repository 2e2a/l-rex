from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'text/$',
        views.TextItemListView.as_view(),
        name='textitems'),
    url(r'text/create/$',
        views.TextItemCreateView.as_view(),
        name='textitem-create'),
    url(r'text/update/(?P<pk>\d+)/$',
        views.TextItemUpdateView.as_view(),
        name='textitem-update'),
    url(r'text/delete/(?P<pk>\d+)/$',
        views.TextItemDeleteView.as_view(),
        name='textitem-delete'),
    url(r'text/(?P<pk>\d+)/$',
        views.TextItemDetailView.as_view(),
        name='textitem'),
    url(r'text-item/$',
        views.TextItemCreateView.as_view(),
        name='textitem'),
    url(r'lists/$',
        views.ListListView.as_view(),
        name='itemlists'),
]