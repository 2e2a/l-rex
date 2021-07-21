from django.urls import path

from . import views


urlpatterns = [
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    path('help/', views.HelpView.as_view(), name='help'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('demo/', views.DemoView.as_view(), name='demo'),
    path('donate/', views.DonateView.as_view(), name='donate'),
    path('invoice/request/', views.InvoiceRequestView.as_view(), name='invoice-request'),
    path('invoice/requested/', views.InvoiceRequestedView.as_view(), name='invoice-requested'),
    path('news/<slug:slug>/', views.NewsView.as_view(), name='news'),
    path('', views.HomeView.as_view(), name='home'),
]