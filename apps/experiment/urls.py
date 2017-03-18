from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^create/$',
        views.SetupCreateView.as_view(),
        name='setup-create'),
    url(r'^(?P<slug>[-\w_]+)/$',
        views.SetupDetailView.as_view(),
        name='setup'),
    url(r'^(?P<setup_slug>[-\w_]+)/exp/create/$',
        views.ExperimentCreateView.as_view(),
        name='experiment-create'),
    url(r'^(?P<setup_slug>[-\w_]+)/exp/(?P<slug>[-\w_]+)/$',
        views.ExperimentDetailView.as_view(),
        name='experiment'),
    url(r'^(?P<setup_slug>[-\w_]+)/exp/(?P<slug>[-\w_]+)/text_item_create/$',
        views.TextItemCreateView.as_view(),
        name='text-item-create'),
    url(r'^(?P<setup_slug>[-\w_]+)/exp/(?P<slug>[-\w_]+)/lists/$',
        views.ListListView.as_view(),
        name='lists'),
]