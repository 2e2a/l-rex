from django.urls import path

from . import views

urlpatterns_experiment = [
    path('pregenerate/', views.ItemPregenerateView.as_view(), name='items-pregenerate'),
    path('upload/', views.ItemUploadView.as_view(), name='items-upload'),
    path('delete-all/', views.ItemDeleteAllView.as_view(), name='items-delete'),
    path('lists/', views.ItemListListView.as_view(), name='itemlists'),
    path('create/text/', views.TextItemCreateView.as_view(), name='text-item-create'),
    path('create/audio-link/', views.AudioLinkItemCreateView.as_view(), name='audio-link-item-create'),
    path('', views.ItemListView.as_view(), name='items'),
]

urlpatterns = [
    path('<slug:item_slug>/update/text/', views.TextItemUpdateView.as_view(), name='text-item-update'),
    path('<slug:item_slug>/update/audio-link/', views.AudioLinkItemUpdateView.as_view(), name='audio-link-item-update'),
    path('<slug:item_slug>/delete/', views.ItemDeleteView.as_view(), name='item-delete'),
    path('<slug:item_slug>/questions/', views.ItemQuestionsUpdateView.as_view(), name='item-questions'),
]