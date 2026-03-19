from django.contrib import admin
from .models import Service, ServiceImage, Appointment


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


admin.site.register(Appointment)
