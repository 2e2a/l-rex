from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'(?P<slug>[-\w_]+)/text_item_create/$',
        views.TextItemCreateView.as_view(),
        name='text-item-create'),
    url(r'(?P<slug>[-\w_]+)/lists/$',
        views.ListListView.as_view(),
        name='lists'),
    url(r'create/$',
        views.ExperimentCreateView.as_view(),
        name='experiment-create'),
    url(r'(?P<slug>[-\w_]+)/$',
        views.ExperimentDetailView.as_view(),
        name='experiment'),
]