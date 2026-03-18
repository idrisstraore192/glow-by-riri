from django.contrib import admin
from .models import Service, Appointment


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration']

    class Media:
        js = ('https://upload-widget.cloudinary.com/latest/global/all.js', 'js/cloudinary_upload.js')


admin.site.register(Appointment)
