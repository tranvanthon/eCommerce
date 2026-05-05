from django.contrib import messages
from tools.utils import get_or_create_cart
from django.shortcuts import render, redirect
from .models import Category, ProductImage, Product, Order, OrderItem, Banner, Brand
from django.shortcuts import get_object_or_404
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    DeleteView,
    UpdateView,
)
from django.db.models import Count, Q, Sum
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy, reverse
from shop.forms import CategoryCreateForm
from django.contrib.messages.views import SuccessMessageMixin
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin:
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied()

        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        if request.user.role in self.allowed_roles:
            return super().dispatch(request, *args, **kwargs)

        return PermissionDenied()


# Check out
def checkout(request):
    order = get_or_create_cart(request)

    if not order.items.exists():
        return redirect("shop:cart_detail")
    context = {
        "order": order,
    }
    return render(request, "shop/checkout.html", context)


# update_from_cart
def update_cart_item(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)

    action = request.POST.get("action")
    try:
        if action == "increase":
            item.quantity += 1

        if action == "decrease":
            item.quantity -= 1

        # Nếu quantity <=0 thì xoá
        if item.quantity <= 0:
            item.delete()
        else:
            item.save()

    except ValidationError:
        messages.warning(request, "Out of stock!!")

    return redirect("shop:cart_detail")


# Delete products in Cart
def remove_from_cart(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)
    item.delete()
    return redirect("shop:cart_detail")


# Cart detail
def cart_detail(request):
    order = get_or_create_cart(request)
    return render(request, "shop/cart_detail.html", {"order": order})


# Cart
def add_to_cart(request, slug):
    product = get_object_or_404(Product, slug=slug)
    order = get_or_create_cart(request)
    order.add_product(product, quantity=1)
    return redirect(request.META.get("HTTP_REFERER", "/"))


# Home
class HomeView(ListView):
    model = Product
    template_name = "shop/index.html"

    def get_queryset(self):
        return Product.active.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        root_categories = Category.active.filter(parent__isnull=True)
        grouped_data = [
            {
                "main_category": cat,
                "groups": cat.get_grouped_products(),
            }
            for cat in root_categories
            if cat.get_grouped_products()
        ]

        # ✅ Dùng property is_bestseller (tính tự động)
        best_sellers = [p for p in Product.active.all() if p.is_bestseller][:8]

        best_sellers = (
            Product.active.filter(order_items__order__status__in=["PAID", "SHIPPED"])
            .annotate(total_sold=Sum("order_items__quantity"))
            .filter(total_sold__gte=50)
            .order_by("-total_sold")[:8]
        )

        # Sản phẩm mới nhất
        latest_products = Product.active.order_by("-created_at")[:8]

        # Banner
        banners = Banner.objects.filter(is_active=True).order_by("order")[:5]

        # Danh mục nổi bật
        featured_categories = (
            Category.active.filter(category_products__isnull=False)
            .annotate(product_count=Count("category_products"))
            .order_by("-product_count")[:4]
        )

        context.update(
            {
                "grouped_categories": grouped_data,
                "best_sellers": best_sellers,
                "latest_products": latest_products,
                "banners": banners,
                "featured_categories": featured_categories,
            }
        )
        return context


class ProductListView(ListView):
    model = Product
    template_name = "shop/product_list.html"
    context_object_name = "products"
    paginate_by = 10

    def get_queryset(self):
        return Product.active.all()


class CategoryDetailView(DetailView):
    model = Category
    template_name = "shop/category_detail.html"
    context_object_name = "category"

    def get_object(self):
        return get_object_or_404(Category.active, slug=self.kwargs["slug"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object

        brand = self.request.GET.get("brand")
        min_p = self.request.GET.get("min_price")
        max_p = self.request.GET.get("max_price")

        context["grouped_products"] = category.get_grouped_products(
            brand=brand, min_price=min_p, max_price=max_p
        )
        context["brands"] = Brand.objects.all()

        context["categories"] = Category.active.filter(parent__isnull=True)
        return context


class CategoryCreateView(RoleRequiredMixin, SuccessMessageMixin, CreateView):
    model = Category
    fields = [
        "name",
        "parent",
        "image",
        "icon_code",
    ]
    success_url = reverse_lazy("shop:home")
    success_message = "Create category successfully!"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create category"
        return context


# Product


@csrf_exempt
@require_POST
def reorder_images(request):
    try:
        data = json.loads(request.body)  # data là list: [{"id": 10, "order": 0}, ...]

        for item in data:
            # Chỉ update ảnh thuộc product mà admin đang quản lý (tăng bảo mật)
            ProductImage.objects.filter(
                id=item["id"],
                # product__in=request.user.products.all()   # nếu có relation
            ).update(order=item.get("order", 0))

        return JsonResponse({"status": "success", "message": "Đã cập nhật thứ tự ảnh"})

    except (json.JSONDecodeError, TypeError, KeyError):
        return JsonResponse(
            {"status": "error", "message": "Dữ liệu gửi lên không hợp lệ"}, status=400
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


class ProductCreateView(RoleRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    fields = ["name", "price", "description", "category", "sku", "cost_price"]
    allowed_roles = ["admin", "staff"]
    success_message = "Create product successfully!"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create product"
        return context


class ProductUpdateView(RoleRequiredMixin, UpdateView):
    model = Product
    fields = ["name", "price", "description", "category"]
    allowed_roles = ["admin", "staff"]


class ProductDeleteView(RoleRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy("shop:product_list")
    allowed_roles = ["admin"]

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return redirect(self.success_url)


class ProductDetailView(DetailView):
    model = Product
    context_object_name = "product"

    def get_object(self):
        return get_object_or_404(Product.active, slug=self.kwargs["slug"])
