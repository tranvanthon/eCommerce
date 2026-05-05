from django.contrib import admin
from shop.models import Brand, Product, Category, ProductImage, Banner


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "product_count", "is_active"]

    readonly_fields = ["product_count"]

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Khi edit
            return self.readonly_fields + ["product_count"]
        return self.readonly_fields


class ProductImageInline(admin.TabularInline):
    """Tabular Inline View for"""

    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]


admin.site.register(Brand)
admin.site.register(Banner)
