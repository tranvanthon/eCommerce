from django.shortcuts import render
from .models import Category, Product
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView


class HomeView(ListView):
    model = Product
    context_object_name = "grouped_categories"
    template_name = "shop/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        root_categories = Category.objects.filter(parent__isnull=True)
        grouped_data = []

        for root_cat in root_categories:
            groups = root_cat.get_grouped_products()
            if groups:  #  Chỉ thêm nhóm nào có sản phẩm
                grouped_data.append(
                    {
                        "main_category": root_cat,
                        "groups": groups,
                    }
                )
            else:
                print(f"-> Bo qua {root_cat.name} vi khong co groups")

        context["grouped_categories"] = grouped_data

        return context


class CategoryDetailView(DetailView):
    model = Category
    context_object_name = "category"

    def get_object(self):
        return Category.objects.get(slug=self.kwargs["slug"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        category = self.object

        products = Product.objects.filter(
            category_id__in=category.get_descendants_ids(), is_active=True
        )

        brand = self.request.GET.get("brand")
        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")

        if brand:
            products = products.filter(category__slug=brand)

        if min_price:
            products = products.filter(price__gte=min_price)

        if max_price:
            products = products.filter(price__lte=max_price)

        if brand or min_price or max_price:
            context["is_filtered"] = True
        else:
            context["is_filtered"] = False
            context["grouped_products"] = category.get_grouped_products()

        context["products"] = products
        context["categories"] = Category.objects.filter(parent__isnull=True)
        context["brands"] = category.children.all()

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
