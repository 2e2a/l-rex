from django.urls import path

from . import views

urlpatterns = [
    path('pregenerate/', views.ItemPregenerateView.as_view(), name='items-pregenerate'),
    path('upload/', views.ItemUploadView.as_view(), name='items-upload'),
    path('delete-all/', views.ItemDeleteAllView.as_view(), name='items-delete'),
    path('delete/<int:pk>/', views.ItemDeleteView.as_view(), name='item-delete'),
    path('create/text/', views.TextItemCreateView.as_view(), name='text-item-create'),
    path('update/text/<int:pk>/', views.TextItemUpdateView.as_view(), name='text-item-update'),
    path('create/audio-link/', views.AudioLinkItemCreateView.as_view(), name='audio-link-item-create'),
    path('update/audio-link/<int:pk>/', views.AudioLinkItemUpdateView.as_view(), name='audio-link-item-update'),
    path('questions/<int:pk>/', views.ItemQuestionsUpdateView.as_view(), name='item-questions'),
    path('', views.ItemListView.as_view(), name='items'),
    path('lists/', views.ItemListListView.as_view(), name='itemlists'),
]