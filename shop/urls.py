from django.urls import path
from shop import views

app_name = "shop"

urlpatterns = [
    path("image/sort/", views.reorder_images, name="reorder-images"),
    path("checkout/", views.checkout, name="checkout"),
    path("cart/update/<int:item_id>", views.update_cart_item, name="cart_update"),
    path("cart/delete/<int:item_id>", views.remove_from_cart, name="cart_delete"),
    path("cart/detail/", views.cart_detail, name="cart_detail"),
    path("cart/add/<slug:slug>/", views.add_to_cart, name="add_to_cart"),
    path("", views.HomeView.as_view(), name="home"),
    path(
        "categories/<slug:slug>/",
        views.CategoryDetailView.as_view(),
        name="category_detail",
    ),
    path(
        "category/create/", views.CategoryCreateView.as_view(), name="category_create"
    ),
    path(
        "category/<slug:slug>/edit",
        views.CategoryCreateView.as_view(),
        name="category_edit",
    ),
    # product
    path("products/", views.ProductListView.as_view(), name="product_list"),
    path("products/create/", views.ProductCreateView.as_view(), name="product_create"),
    path(
        "products/<slug:slug>/",
        views.ProductDetailView.as_view(),
        name="product_detail",
    ),
    path(
        "products/edit/<slug:slug>/",
        views.ProductUpdateView.as_view(),
        name="product_update",
    ),
    path(
        "products/delete/<slug:slug>/",
        views.ProductDeleteView.as_view(),
        name="product_delete",
    ),
]
