from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.conf import settings
from django.db.models import Sum, Count

from PIL import Image
from decimal import Decimal
from tools.path import get_upload_path


class Banner(models.Model):
    name = models.CharField(max_length=255)
    link = models.URLField(blank=True)
    order = models.IntegerField(blank=True)
    image = models.ImageField(upload_to=get_upload_path)
    is_active = models.BooleanField(default=True, db_default=True)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Brand.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def total_sold(self):
        """Tổng số lượng đã bán của thương hiệu"""
        return (
            OrderItem.objects.filter(
                product__brand=self, order__status__in=["PAID", "SHIPPED"]
            ).aggregate(total=Sum("quantity"))["total"]
            or 0
        )

    @property
    def product_count(self):
        """Số lượng sản phẩm đang active của thương hiệu"""
        return self.brand_brands.filter(is_active=True).count()


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Category(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, blank=True, related_name="children", null=True
    )
    slug = models.SlugField(unique=True, blank=True)
    icon_code = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to=get_upload_path, blank=True)

    # status and show
    is_active = models.BooleanField(default=True, db_default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    # SEO
    meta_title = models.CharField(max_length=200, blank=True, verbose_name="Meta Title")
    meta_description = models.TextField(
        max_length=500, blank=True, verbose_name="Meta Description"
    )
    meta_keywords = models.CharField(
        max_length=300, blank=True, verbose_name="Meta Keywords"
    )

    # Timestamps
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    # Gọi manager
    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(fields=["name", "is_active"]),
            models.Index(fields=["parent", "is_active"]),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def get_absolute_url(self):
        return reverse("shop:category_detail", kwargs={"slug": self.slug})

    @property
    def product_count(self):
        """Tổng số sản phẩm (tính cả category con)"""
        descendant_ids = self.get_descendants_ids()
        return Product.active.filter(category_id__in=descendant_ids).count()

    @product_count.setter
    def product_count(self, value):
        import warnings

        warnings.warn(
            "Setting product_count manually is deprecated. This value is auto-calculated."
        )
        pass

    @property
    def total_sold(self):
        """Tổng số lượng đã bán của category (tính cả category con)"""
        descendant_ids = self.get_descendants_ids()
        return (
            OrderItem.objects.filter(
                product__category_id__in=descendant_ids,
                order__status__in=["PAID", "SHIPPED"],
            ).aggregate(total=Sum("quantity"))["total"]
            or 0
        )

    def delete(self, *args, **kwargs):
        """Vô hiệu hoá thay vì xoá"""
        if self.category_products.filter(is_active=True).exists():
            raise ValidationError("Cannot delete category with active products")
        self.is_active = False
        self.save(update_fields=["is_active"])

    def hard_delete(self, *args, **kwargs):
        """Xoá thật"""
        super().delete(*args, **kwargs)

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

        for child in self.children.filter(is_active=True):
            descendants.append(child)
            descendants.extend(child.get_descendants())

        return descendants

    def get_descendants_ids(self):
        """Lấy list ID của tất cả descendants (để filter Product)"""
        return [cat.id for cat in self.get_descendants(include_self=True)]

    def get_grouped_products(self, brand=None, min_price=None, max_price=None):
        """Lấy sản phẩm theo nhóm danh mục CON"""
        if self.children.exists():
            result = []
            for child in self.children.filter(is_active=True):
                descendant_ids = child.get_descendants_ids()
                products = Product.active.filter(category_id__in=descendant_ids)
                if brand:
                    products = products.filter(brand__slug=brand)
                if min_price:
                    products = products.filter(price__gte=min_price)
                if max_price:
                    products = products.filter(price__lte=max_price)

                if products.exists():
                    result.append(
                        {
                            "category": child,
                            "products": products.distinct(),
                        }
                    )
            return result
        else:
            products = self.category_products.filter(is_active=True)
            if brand:
                products = products.filter(brand__slug=brand)
            if min_price:
                products = products.filter(price__gte=min_price)
            if max_price:
                products = products.filter(price__lte=max_price)
            if products.exists():
                return [{"category": self, "products": products}]
            return []


class Product(models.Model):
    class ColorChoice(models.TextChoices):
        BLACK = "BLACK", "Black"
        GOLD = "GOLD", "Gold"
        RED = "RED", "Red"

    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="category_products"
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="brand_brands",
        null=True,
        blank=True,
    )
    slug = models.SlugField(unique=True, blank=True)

    # Mô tả sản phẩm
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=300, blank=True)

    # Thông tin giá và tồn kho
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=0, default=0)
    cost_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Import price", default=10.00
    )
    sku = models.CharField(max_length=100, unique=True, verbose_name="Code SKU")
    barcode = models.CharField(
        max_length=100, blank=True, verbose_name="Barcode", db_index=True
    )

    # Quản lý tồn kho
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    low_stock_threshold = models.PositiveIntegerField(
        default=5, verbose_name="Low inventory alert threshold"
    )
    track_stock = models.BooleanField(default=True, verbose_name="Inventory tracking")

    # Trạng thái sản phẩm
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, verbose_name="Product is featured")

    # Thông số kỹ thuật
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Weight (kg)",
    )
    dimensions = models.CharField(
        max_length=100, blank=True, verbose_name="Dimensions (width x height x depth)"
    )
    color = models.CharField(
        max_length=20, choices=ColorChoice.choices, default=ColorChoice.BLACK
    )
    material = models.CharField(max_length=50, blank=True, verbose_name="Material")

    # SEO
    meta_title = models.CharField(max_length=200, blank=True, verbose_name="Meta Title")
    meta_description = models.TextField(
        max_length=500, blank=True, verbose_name="Meta Description"
    )
    meta_keywords = models.CharField(
        max_length=300, blank=True, verbose_name="Meta Keywords"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date publish")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date update")

    # Gọi manager
    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name", "is_active"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("shop:product_detail", kwargs={"slug": self.slug})

    @property
    def price_sale(self):
        """Giá sau khi giảm giá"""
        if self.discount_percent == 0:
            return self.price
        discount_amount = (self.price * self.discount_percent) / Decimal("100")
        return self.price - discount_amount

    @property
    def is_in_stock(self):
        """Kiểm tra còn hàng không"""
        return self.stock > 0 if self.track_stock else True

    @property
    def is_low_stock(self):
        """Kiểm tra hàng sắp hết"""
        return self.track_stock and self.stock <= self.low_stock_threshold

    @property
    def view_count(self):
        """Số lượt xem - tính từ bảng riêng (nên tạo sau)"""
        # Tạm thời trả về 0, sau này có thể tracking bằng middleware
        return 0

    @property
    def sold_count(self):
        """Tổng số lượng đã bán (từ OrderItem)"""
        total = self.order_items.filter(
            order__status__in=["PAID", "SHIPPED"]
        ).aggregate(total=Sum("quantity"))["total"]
        return total or 0

    @property
    def is_bestseller(self):
        """Tự động xác định bestseller (bán > 50 sản phẩm)"""
        return self.sold_count >= 50

    @property
    def total_revenue(self):
        """Tổng doanh thu từ sản phẩm này"""
        revenue = self.order_items.filter(
            order__status__in=["PAID", "SHIPPED"]
        ).aggregate(total=Sum("subtotal"))["total"]
        return revenue or 0

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


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to=get_upload_path)
    is_main = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        verbose_name = "ProductImage"
        verbose_name_plural = "Images of products"
        ordering = ["order"]

    def save(self, *args, **kwargs):
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if old.image == self.image:
                return super().save(*args, **kwargs)

        super().save(*args, **kwargs)

        if self.image:
            try:
                img = Image.open(self.image.path)
                if img.width > 800 or img.height > 800:
                    img.thumbnail((800, 800))
                img.save(self.image.path, optimize=True, quality=70)
            except FileNotFoundError:
                print("Image file not found, skip processing")

    @property
    def imageURL(self):
        if self.image:
            return self.image.url
        return "/static/images/default/default.png"

    def __str__(self):
        return f"{self.product.name} image"


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PAID = "PAID", "Paid"
        SHIPPED = "SHIPPED", "Shipped"
        CANCELLED = "CANCELLED", "Cancelled"

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        blank=True,
        null=True,
    )
    complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(complete=False),
                name="unique_active_cart_per_user",
            )
        ]

    def can_be_cancelled(self):
        return self.status in [self.Status.DRAFT, self.Status.PAID]

    def add_product(self, product, quantity=1):
        item, created = self.items.get_or_create(
            product=product, defaults={"price": product.price_sale}
        )
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()

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

    def complete_order(self):
        """Xác nhận đơn hàng thành công - Cập nhật stock"""
        if self.status != self.Status.DRAFT:
            return False

        for item in self.items.all():
            if item.product.track_stock:
                if item.product.stock < item.quantity:
                    raise ValidationError(f"Insufficient stock for {item.product.name}")
                item.product.stock -= item.quantity
                item.product.save()

        self.complete = True
        self.status = self.Status.PAID
        self.save()
        return True

    @property
    def get_total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_items(self):
        return self.items.aggregate(total=Sum("quantity"))["total"] or 0


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="order_items"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        indexes = [
            models.Index(fields=["order", "product"]),
        ]

    @property
    def subtotal(self):
        return self.price * self.quantity

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")
        if self.product.track_stock and self.product.stock < self.quantity:
            raise ValidationError(f"Only {self.product.stock} items available")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
