from django.urls import path
from .views import booking_page, booking_success, booking_deposit_success, booking_deposit_cancel

urlpatterns = [
    path("", booking_page, name="booking"),
    path("success/", booking_success, name="booking_success"),
    path("deposit/success/", booking_deposit_success, name="booking_deposit_success"),
    path("deposit/cancel/", booking_deposit_cancel, name="booking_deposit_cancel"),
]
