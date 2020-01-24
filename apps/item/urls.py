from django.urls import path

from . import views

urlpatterns_materials = [
    path('pregenerate/', views.ItemPregenerateView.as_view(), name='items-pregenerate'),
    path('upload/feedback', views.ItemFeedbackUploadView.as_view(), name='items-upload-feedback'),
    path('upload/', views.ItemUploadView.as_view(), name='items-upload'),
    path('download/', views.ItemCSVDownloadView.as_view(), name='items-download'),
    path('delete-all/', views.ItemDeleteAllView.as_view(), name='items-delete'),
    path('lists/', views.ItemListListView.as_view(), name='itemlists'),
    path('lists/upload/', views.ItemListUploadView.as_view(), name='itemlist-upload'),
    path('lists/download/', views.ItemListCSVDownloadView.as_view(), name='itemlist-download'),
    path('create/', views.ItemCreateView.as_view(), name='item-create'),
    path('create/text/', views.TextItemCreateView.as_view(), name='text-item-create'),
    path('create/markdown/', views.MarkdownItemCreateView.as_view(), name='markdown-item-create'),
    path('create/audio-link/', views.AudioLinkItemCreateView.as_view(), name='audio-link-item-create'),
    path('', views.ItemListView.as_view(), name='items'),
]

urlpatterns = [
    path('<slug:item_slug>/update/', views.ItemUpdateView.as_view(), name='item-update'),
    path('<slug:item_slug>/update/text/', views.TextItemUpdateView.as_view(), name='text-item-update'),
    path('<slug:item_slug>/update/markdown/', views.MarkdownItemUpdateView.as_view(), name='markdown-item-update'),
    path('<slug:item_slug>/update/audio-link/', views.AudioLinkItemUpdateView.as_view(), name='audio-link-item-update'),
    path('<slug:item_slug>/delete/', views.ItemDeleteView.as_view(), name='item-delete'),
    path('<slug:item_slug>/questions/', views.ItemQuestionsUpdateView.as_view(), name='item-questions'),
    path('<slug:item_slug>/feedback/', views.ItemFeedbackUpdateView.as_view(), name='item-feedback'),
]