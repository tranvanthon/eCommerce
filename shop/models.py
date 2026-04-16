from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db.models import Prefetch
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, related_name="children", blank=True, null=True
    )
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        # Đảm bảo mỗi user chỉ 1 cart được active
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(complete=False),
                name="unique_active_cart_per_user",
            )
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def get_absolute_url(self):
        return reverse("shop:category_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_descendants(self, include_self=False):
        """Lấy tất cả danh mục con, cháu, chắt..."""
        descendants = []
        if include_self:
            descendants.append(self)

        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())

        return descendants

    def get_descendants_ids(self):
        """Lay list ID cua all descendants (de fielter Product)"""
        return [cat.id for cat in self.get_descendants(include_self=True)]

    def get_grouped_products(self):
        """Lấy sản phẩm theo nhóm danh mục CON, bao gồm cả chính nó"""
        if self.children.exists():

            children = self.children.prefetch_related(
                Prefetch("products", queryset=Product.objects.filter(is_active=True))
            )

            result = []
            # Lấy sản phẩm trực tiếp từ danh mục con
            for child in children:
                products = child.products.filter(is_active=True)

                if products:
                    result.append({"category": child, "products": products})

            return result
        else:
            # Nếu không có children, lấy sản phẩm của chính nó
            products = self.products.filter(is_active=True)
            if products:
                return [
                    {
                        "category": self,
                        "products": products,
                    }
                ]


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    price = models.DecimalField(decimal_places=2, max_digits=9)
    is_active = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    # Sock status
    def is_in_stock(self):
        return self.stock > 0 and self.is_active

    # Validation
    def clean(self):
        if self.price <= 0:
            raise ValidationError("Price must be greater than zero")
        if self.stock < 0:
            raise ValidationError("Stock cannot be negative")

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Order(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PAID = "PAID", "Paid"
        SHIPPED = "SHIPPED", "Shipped"
        CANCELLED = "CANCELLED", "Cancelled"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="customer", blank=True, null=True
    )
    complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def can_be_cancelled(self):
        return self.status in [
            self.Status.DRAFT,
            self.Status.PAID,
        ]

    # Thêm sản phẩm vào cart
    def add_product(self, product, quantity=1):
        item, created = self.items.get_or_create(
            product=product, defaults={"price": product.price}
        )

        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()

    # Cập nhật giỏ hàng
    def update_item(self, product, quantity=1):
        try:
            item = self.items.get(product=product)
            if quantity <= 0:
                item.delete()
            else:
                item.quantity = quantity
                item.save()

        except OrderItem.DoesNotExist:
            pass

    @property
    def get_total(self):
        return sum(item.subtotal for item in self.items.all())

    class Meta:
        ordering = ["-created_at"]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    @property
    def subtotal(self):
        return self.price * self.quantity

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")
        if not self.product.is_in_stock():
            raise ValidationError("Product is out of stock")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
