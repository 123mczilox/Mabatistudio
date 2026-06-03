from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('gallery/', views.gallery, name='gallery'),
    path('contact/', views.contact, name='contact'),
    path('products/', views.products, name='products'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('roof-calculator/', views.roof_calculator, name='roof_calculator'),
    path('roof-estimates/', views.quote_history, name='quote_history'),
    path('roof-estimates/<slug:quote_number>/', views.quote_detail, name='quote_detail'),
    path('about/', views.about, name='about'),
]