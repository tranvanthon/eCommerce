from django.shortcuts import render
from .models import Category, Product
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView


class HomeView(ListView):
    model = Product
    context_object_name = "products"
    template_name = "shop/index.html"

    def get_queryset(self):
        return Product.objects.filter(is_active=True).order_by("-created_at")[:8]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(parent__isnull=True)
        return context

    # categories = Category.objects.filter(parent__isnull=True)  # show category in navbar
    # featured_products = Product.objects.filter(is_active=True).order_by("-created_at")[
    #     :8
    # ]  # Products featured
    # latest_products = Product.objects.filter(is_active=True).order_by("-stock")[
    #     :8
    # ]  # Latest products

    # context = {
    #     "categories": categories,
    #     "featured_products": featured_products,
    #     "latest_products": latest_products,
    # }
    # return render(request, "shop/index.html", context)


# Category list view chỉ lấy gốc (cho menu chính)
# class CategoryListView(ListView):
#     model = Category
#     context_object_name = "categories"

#     def get_queryset(self):
#         return Category.objects.filter(parent__isnull=True)


class CategoryDetailView(DetailView):
    model = Category
    context_object_name = "category"

    def get_object(self):
        return Category.objects.get(slug=self.kwargs["slug"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["grouped_products"] = self.object.get_grouped_products()
        context["categories"] = self.object.get_descendants()

        return context


class ProductListView(ListView):
    model = Product
    context_object_name = "products"
    paginate_by = 10

    def get_queryset(self):
        return Product.objects.filter(is_active=True)


class ProductDetailView(DetailView):
    model = Product
    context_object_name = "product"

    def get_object(self):
        return Product.objects.get(slug=self.kwargs["slug"])


# class ProductListView(ListView):
#     model = Product
#     context_object_name = "products"
#     ordering = ["-created_at"]

#     def get_queryset(self):
#         """Lọc sản phẩm active + theo category nếu có slug"""
#         queryset = Product.objects.filter(is_active=True)

#         slug = self.kwargs.get("slug")  # get from url
#         if slug:
#             Category = get_object_or_404(Category, slug=slug)

#         return queryset

#     def get_context_data(self, *args, **kwargs):
#         context = super().get_context_data(*args, **kwargs)
#         categories_nav = Category.objects.filter(parent__isnull=True)
#         products = Product.objects.filter(is_active=True).order_by("-created_at")

#         context["categories_nav"] = categories_nav
#         context["products"] = products
#         return context
