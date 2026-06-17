from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('gallery/', views.gallery, name='gallery'),
    path('contact/', views.contact, name='contact'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
    path('products/', views.products, name='products'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('roof-calculator/', views.roof_calculator, name='roof_calculator'),
    path('roof-calculator/request-quote/', views.request_quote, name='request_quote'),
    path('roof-calculator/quote-confirmation/<slug:quote_number>/', views.quote_confirmation, name='quote_confirmation'),
    path('about/', views.about, name='about'),
]