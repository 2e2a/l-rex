from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<slug>[-\w_]+)/$',
        views.ExperimentDetailView.as_view(),
        name='experiment'),
]