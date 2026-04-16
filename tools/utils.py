from shop.models import Order


def get_or_create_cart(request):
    # Uu tien cho user login
    if request.user.is_authenticated:
        order = Order.objects.filter(user=request.user, complete=False).first()
        if not order:
            order = Order.objects.create(user=request.user, complete=False)
        request.session["cart_id"] = order.id
        return order

    cart_id = request.session.get("cart_id")

    if cart_id:
        try:
            return Order.objects.get(id=cart_id, complete=False)
        except Order.DoesNotExist:
            pass

    # chưa có cart → tạo mới cho guest
    order = Order.objects.create(complete=False)
    request.session["cart_id"] = order.id
    return order
