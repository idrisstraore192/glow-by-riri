
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("admin/dashboard/", core_views.admin_dashboard, name="admin_dashboard"),
    path("admin/booking/calendar/", core_views.booking_calendar, name="booking_calendar"),
    path("", include("core.urls")),
    path("shop/", include("shop.urls")),
    path("booking/", include("booking.urls")),
    path("avis/", include("reviews.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
