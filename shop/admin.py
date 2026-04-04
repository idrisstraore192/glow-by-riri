from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from .models import Product, ProductImage, ProductVideo, ProductVariant, Order, OrderItem, TutorialVideo


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
    list_display = ['id', 'customer_name', 'customer_email', 'total', 'paid', 'shipped', 'created_at']
    list_filter = ['paid', 'shipped']
    readonly_fields = ['stripe_session_id', 'created_at', 'shipping_address']
    fields = ['customer_name', 'customer_email', 'total', 'paid', 'shipped', 'tracking_number', 'shipping_address', 'stripe_session_id', 'created_at']
    inlines = [OrderItemInline]

    def save_model(self, request, obj, form, change):
        was_shipped = change and Order.objects.filter(pk=obj.pk, shipped=True).exists()
        super().save_model(request, obj, form, change)
        if obj.shipped and not was_shipped and obj.customer_email:
            tracking_info = f"\nNuméro de suivi : {obj.tracking_number}" if obj.tracking_number else ""
            message = f"""Bonjour {obj.customer_name} ✦

Bonne nouvelle — ta commande #{obj.id} a été expédiée ! 📦{tracking_info}

Tu peux suivre l'état de ta commande ici :
https://glowbyriri.up.railway.app/shop/suivi/

Si tu as des questions, réponds à cet email ou écris-nous à glowbyririi@gmail.com.

À bientôt,
Riri — Glow by Riri 💕
"""
            try:
                send_mail(
                    subject=f"📦 Ta commande #{obj.id} est en route — Glow by Riri",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[obj.customer_email],
                    fail_silently=True,
                )
            except Exception:
                pass


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['order', 'name', 'display_type', 'price', 'display_discount', 'disponible']
    list_display_links = ['name']
    list_editable = ['order', 'disponible']
    list_filter = ['product_type', 'disponible']
    ordering = ['order', 'product_type', 'price']
    fields = ['name', 'product_type', 'category', 'disponible', 'order', 'price', 'discount_percent', 'description', 'image_url', 'video_url']
    inlines = [ProductImageInline, ProductVideoInline, ProductVariantInline]

    def display_type(self, obj):
        return obj.get_product_type_display()
    display_type.short_description = "Type"

    def display_discount(self, obj):
        if obj.discount_percent and obj.discount_percent > 0:
            return f"-{obj.discount_percent:.0f}%"
        return "—"
    display_discount.short_description = "Rabais"

    class Media:
        js = ('https://upload-widget.cloudinary.com/latest/global/all.js', 'js/cloudinary_upload.js')



@admin.register(TutorialVideo)
class TutorialVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'product', 'badge', 'order']
    list_editable = ['order']
    fields = ['title', 'video_url', 'product', 'badge', 'order', 'section']
