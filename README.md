* Tạo trang chủ có danh mục theo sản phẩm
* Trong views.py
* class HomeView(ListView):
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
  *urls.py
  path('', views.HomeView.as_view(), name='home')
* Trong template:
* {% extends 'base.html' %}

{% block title %}
    
{% endblock title %}

{% block content %}
<div class="homepage">
    {% for category_group in grouped_categories %}
        {# Phần hiển thị cho một danh mục cha, ví dụ: Dụng cụ mỹ thuật #}
        <div class="category-section" style="margin-bottom: 40px;">
            <h1 style="border-bottom: 2px solid #ee4d2d; padding-bottom: 10px;">
                {{ category_group.main_category.name }}
            </h1>
            
            {# Duyệt qua các nhóm sản phẩm bên trong danh mục cha này #}
            {% for group in category_group.groups %}
                <div style="margin-top: 30px;">
                    <h2 style="display: flex; justify-content: space-between;">
                        <span>{{ group.category.name }}</span>
                        <a href="{% url 'shop:category_detail' group.category.slug %}">
                            Xem tất cả →
                        </a>
                    </h2>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 10px;">
                    {% for product in group.products %}
                        <div style="border:1px solid #ddd; padding:10px; border-radius:6px;">
                            <a href="{% url 'shop:product_detail' product.slug %}">
                                <h4 style="font-size:14px;">{{ product.name }}</h4>
                            </a>
                            <p style="color:red; font-weight:bold;">{{ product.price }} đ</p>
                            <p>
                                {% if product.is_in_stock %}
                                    <span style="color:green;">Còn hàng</span>
                                {% else %}
                                    <span style="color:gray;">Hết hàng</span>
                                {% endif %}
                            </p>
                            <button style="margin-top:8px; width:100%; padding:6px; background:#ee4d2d; color:white; border:none; cursor:pointer;">
                                Thêm vào giỏ
                            </button>
                        </div>
                    {% endfor %}
                </div>
            {% empty %}
                <p>Chưa có sản phẩm trong danh mục này</p>
            {% endfor %}
        </div>
    {% endfor %}
</div>
{% endblock %}
###################################
Tạo sản phẩm theo category:
from django.views.generic import ListView, DetailView
class CategoryDetailView(DetailView):
    #code
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
