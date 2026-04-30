from django import forms
from shop.models import Category
class CategoryCreateForm(forms.ModelForm):
    modeld = Category
    fields = ['name', 'parent', 'image', 'icon_code',]
    