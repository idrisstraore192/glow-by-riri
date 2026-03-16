from django.contrib import admin
from .models import Product, Order, OrderItem


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


admin.site.register(Product)
