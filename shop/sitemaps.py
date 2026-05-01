from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product


class StaticSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['home', 'products', 'booking', 'cart']

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    priority = 0.6
    changefreq = 'weekly'

    def items(self):
        return Product.objects.filter(available=True)

    def location(self, obj):
        return reverse('product_detail', args=[obj.id])
