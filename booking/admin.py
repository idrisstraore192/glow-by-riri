from django.contrib import admin
from .models import Service, ServiceImage, Appointment, AvailabilitySlot


class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    fields = ['image_url', 'order']

    class Media:
        js = ('https://upload-widget.cloudinary.com/latest/global/all.js', 'js/cloudinary_upload.js')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'display_discount', 'duration']
    list_filter = ['category']
    fields = ['name', 'category', 'price', 'discount_percent', 'duration', 'description']
    inlines = [ServiceImageInline]

    def display_discount(self, obj):
        if obj.discount_percent and obj.discount_percent > 0:
            return f"-{obj.discount_percent:.0f}%"
        return "—"
    display_discount.short_description = "Rabais"

    class Media:
        js = ('https://upload-widget.cloudinary.com/latest/global/all.js', 'js/cloudinary_upload.js')


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'date', 'time', 'is_booked']
    list_filter = ['is_booked', 'date']
    list_editable = ['is_booked']
    ordering = ['date', 'time']
    date_hierarchy = 'date'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'customer_email', 'service', 'date', 'time', 'deposit_paid']
    list_filter = ['deposit_paid', 'date']
    readonly_fields = ['stripe_session_id', 'deposit_paid', 'slot']
    ordering = ['-date', '-time']
