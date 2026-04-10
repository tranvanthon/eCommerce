from django.urls import path
from shop import views
app_name = 'shop'

urlpatterns = [
    path('', views.index, name='home'),
    path('products/', views.ProductListView.as_view(), name='product_list'), # all product
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
]
