from django.urls import path

from . import views

urlpatterns = [
    path('pregenerate/', views.ItemPregenerateView.as_view(), name='items-pregenerate'),
    path('upload/', views.TextItemUploadView.as_view(), name='textitem-upload'),
    path('delete-all/', views.TextItemDeleteAllView.as_view(), name='textitems-delete'),
    path('create/', views.TextItemCreateView.as_view(), name='textitem-create'),
    path('update/<int:pk>/', views.TextItemUpdateView.as_view(), name='textitem-update'),
    path('delete/<int:pk>/', views.TextItemDeleteView.as_view(), name='textitem-delete'),
    path('', views.TextItemListView.as_view(), name='textitems'),
    path('lists/$', views.ItemListListView.as_view(), name='itemlists'),
]