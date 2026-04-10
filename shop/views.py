from django.shortcuts import render
from .models import Category, Product
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView

def index(request):

    categories = Category.objects.filter(parent__isnull = True)#show category in navbar
    featured_products = Product.objects.filter(is_active = True).order_by('-created_at')[:8]#Products featured 
    latest_products = Product.objects.filter(is_active=True).order_by('-stock')[:8] #Latest products

    context ={
        'categories':categories,
        'featured_products': featured_products,
        'latest_products':latest_products,
    }
    return render(request, 'shop/index.html', context)

class ProductListView(ListView):   
    model = Product
    fields = '__all__'
    context_object_name = 'products'
    ordering = ['-created_at']
    def get_queryset(self):
        """Lọc sản phẩm active + theo category nếu có slug"""
        queryset = Product.objects.filter(is_active=True)
        
        slug = self.kwargs.get('slug') # get from url
        if slug:
            Category =get_object_or_404(Category, slug=slug)
            

        return queryset

    def get_context_data(self,*args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        categories_nav = Category.objects.filter(parent__isnull=True)
        products = Product.objects.filter(is_active=True).order_by('-created_at')


        context["categories_nav"] = categories_nav
        context["products"] = products
        return context
    
class ProductDetailView(DetailView):
    model = Product
    fields = ['name', 'price', 'stock']
    context_object_name = 'products'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'



# def product_list(request, slug=None):
#     products = Product.objects.filter(is_active=True).order_by('-created_at')
#     categories_nav = Category.objects.filter(parent__isnull = True)#show category in navbar
#     category = None
#     categories_current = None # Show breadcrumb after

#     if slug:
#         category = get_object_or_404(Category, slug = slug)
#         # Get all category IDs + descendants
#         descendant_ids = category.get_descendants_ids()
#         products = products.filter(category__id__in=descendant_ids)
#         categories_current = category

    
#     context ={
#         'categories_nav': categories_nav,
#         'categories_current': categories_current,
#         'products': products,
#         'categories':Category.objects.filter(parent__isnull=True)
#     }
#     return render(request, 'shop/product_list.html', context)

