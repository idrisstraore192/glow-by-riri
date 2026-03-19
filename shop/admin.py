from django.contrib import admin
from .models import Product, ProductImage, ProductVariant, Order, OrderItem


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image_url', 'order']

    class Media:
        js = ('https://upload-widget.cloudinary.com/latest/global/all.js', 'js/cloudinary_upload.js')


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['size', 'price']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'price', 'quantity']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'customer_email', 'total', 'paid', 'created_at']
    list_filter = ['paid']
    readonly_fields = ['stripe_session_id', 'created_at']
    inlines = [OrderItemInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price']
    inlines = [ProductImageInline, ProductVariantInline]

    class Media:
        js = ('https://upload-widget.cloudinary.com/latest/global/all.js', 'js/cloudinary_upload.js')
