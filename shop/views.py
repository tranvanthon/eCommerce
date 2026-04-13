from django.contrib import messages

from django.shortcuts import render, redirect
from .models import Category, Product, Order, OrderItem
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.core.exceptions import ValidationError


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
    order_id = request.session.get("order_id")

    if not order_id:
        return render(request, "shop/cart_detail.html", {"order": None})
    order = Order.objects.get(id=order_id)

    return render(request, "shop/cart_detail.html", {"order": order})


# Cart
def add_to_cart(request, slug):
    product = get_object_or_404(Product, slug=slug)
    # Lấy order tron session
    order_id = request.session.get("order_id")

    if order_id:
        order = Order.objects.get(id=order_id)
    else:
        order = Order.objects.create(status=Order.Status.DRAFT, total_price=0)
        request.session["order_id"] = order.id
    try:
        # Kiểm tra product đã có trong giỏ hàng chưa
        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            product=product,
            defaults={"price": product.price, "quantity": 1},
        )
        # Nếu đã có hàng thì tăng quantity
        if not created:
            order_item.quantity += 1
            order_item.save()
    except ValidationError as e:
        messages.warning(request, f"Product is out of stock. {e}")
        return redirect("shop:home")

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
        context["quantity_order_item"] = OrderItem.objects.all()
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


# Category and product
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
