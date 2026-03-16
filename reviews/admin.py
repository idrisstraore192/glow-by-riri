from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating', 'approved', 'created_at']
    list_editable = ['approved']
    list_filter = ['approved', 'rating']
    ordering = ['-created_at']
