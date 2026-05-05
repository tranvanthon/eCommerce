from django import forms
from shop.models import Category


# Tạo Mixin chuẩn cho user để phục vụ cho product
class CategoryCreateForm(forms.ModelForm):
    class Meta:
        modeld = Category
        fields = ["name", "parent", "image", "icon_code", "description"]
