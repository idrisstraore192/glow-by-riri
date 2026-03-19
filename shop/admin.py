from django.contrib import admin
from .models import Product, ProductImage, ProductVideo, ProductVariant, Order, OrderItem


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image_url', 'order']

    class Media:
        js = ('https://upload-widget.cloudinary.com/latest/global/all.js', 'js/cloudinary_upload.js')


class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 1
    fields = ['video_url', 'order']

    class Media:
        js = ('https://upload-widget.cloudinary.com/latest/global/all.js', 'js/cloudinary_upload.js')


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['variant_type', 'label', 'price']


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
    list_display = ['name', 'category', 'price', 'display_discount']
    list_filter = ['category']
    fields = ['name', 'category', 'product_type', 'price', 'discount_percent', 'description']
    inlines = [ProductImageInline, ProductVideoInline, ProductVariantInline]

    def display_discount(self, obj):
        if obj.discount_percent and obj.discount_percent > 0:
            return f"-{obj.discount_percent:.0f}%"
        return "—"
    display_discount.short_description = "Rabais"

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        if request.GET.get('category'):
            initial['category'] = request.GET.get('category')
        return initial

    class Media:
        js = ('https://upload-widget.cloudinary.com/latest/global/all.js', 'js/cloudinary_upload.js')
