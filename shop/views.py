from django.contrib import messages
from tools.utils import get_or_create_cart
from django.shortcuts import render, redirect
from .models import Category, Product, Order, OrderItem
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from shop.forms import CategoryCreateForm


# Check out
def checkout(request):
    order = get_or_create_cart(request)

    if not order.items.exists():
        return redirect("shop:cart_detail")
    context = {
        "order": order,
    }
    return render(request, "shop/checkout.html", context)
    # order_id = request.session.get("order_id")

    # if not order_id:
    #     messages.error(request, "Empty cart!")
    #     return redirect("shop:cart_detail")

    # order = Order.objects.get(id=order_id)

    # if not order.items.exists():
    #     messages.error(request, "Empty cart")
    #     return redirect("shop:cart_detail")

    # try:
    #     # test va tru stock
    #     for item in order.items.all():
    #         product = item.product
    #         if item.quantity > product.stock:
    #             raise ValidationError(f"{product.name} insufficient stock")
    #         product.stock -= item.quantity
    #         product.save()
    #     # update order
    #     order.status = Order.Status.PAID
    #     order.total_price = order.get_total()
    #     order.save()

    #     # delete session cart
    #     del request.session["order_id"]

    #     messages.success(request, "Order placed successfully!")
    #     return redirect("shop:home")
    # except ValidationError as e:
    #     messages.error(request, str(e))
    #     return redirect("shop:cart_detail")


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
        context["categories"] = root_categories
        return context


class CatgoryListView(ListView):
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
    template_name = "shop/category_detail.html"  # Đảm bảo đúng path template
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        # Lấy query params
        brand = self.request.GET.get("brand")
        min_p = self.request.GET.get("min_price")
        max_p = self.request.GET.get("max_price")

        # # Truyền vào hàm model
        context["grouped_products"] = category.get_grouped_products(
            brand=brand, min_price=min_p, max_price=max_p
        )
        context["categories"] = Category.objects.filter(parent__isnull=True)

        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    success_url = reverse_lazy("shop:dashboard")
    form_class = CategoryCreateForm


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
