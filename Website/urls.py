from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('gallery/', views.gallery, name='gallery'),
    path('contact/', views.contact, name='contact'),
    path('products/', views.products, name='products'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('visualizer/', views.visualizer, name='visualizer'),
    path('about/', views.about, name='about'),
]