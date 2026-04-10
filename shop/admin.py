from django.contrib import admin
from shop.models import Product, Category

admin.site.register(Product)
admin.site.register(Category)

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
