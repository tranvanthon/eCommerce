from django.urls import path
from shop import views
app_name = 'shop'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    # path('category/', views.CategoryListView.as_view(), name='category_list'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('products/', views.ProductListView.as_view(), name='product_list'), # all product
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
]
