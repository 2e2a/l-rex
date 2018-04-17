from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^pregenerate/$',
        views.ItemPregenerateView.as_view(),
        name='items-pregenerate'),
    url(r'^text/$',
        views.TextItemListView.as_view(),
        name='textitems'),
    url(r'^text/upload/$',
        views.TextItemUploadView.as_view(),
        name='textitem-upload'),
    url(r'^text/delete-all/$',
        views.TextItemDeleteAllView.as_view(),
        name='textitems-delete'),
    url(r'^text/create/$',
        views.TextItemCreateView.as_view(),
        name='textitem-create'),
    url(r'^text/update/(?P<pk>\d+)/$',
        views.TextItemUpdateView.as_view(),
        name='textitem-update'),
    url(r'^text/delete/(?P<pk>\d+)/$',
        views.TextItemDeleteView.as_view(),
        name='textitem-delete'),
    url(r'^lists/$',
        views.ItemListListView.as_view(),
        name='itemlists'),
]