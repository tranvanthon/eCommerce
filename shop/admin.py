from django.contrib import admin
from shop.models import Brand, Product, Category

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Brand)

# class ProductInline(admin.TabularInline):
#     model = Product
#     extra = 3
#     list_display = [
#         "name",
#         "category",
#         "price",
#         "stock",
#     ]


# class CategoryAdmin(admin.ModelAdmin):
#     list_display = [
#         "name",
#         "parent",
#     ]

#     inlines = [ProductInline]


# admin.site.register(Category, CategoryAdmin)
