from django.urls import path
from . import views

urlpatterns = [
    path("", views.product_list, name="products"),
    path("<int:product_id>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/remove-item/<str:item_key>/", views.remove_cart_item, name="remove_cart_item"),
    path("cart/update/<int:product_id>/", views.update_cart, name="update_cart"),
    path("cart/update-item/<str:item_key>/", views.update_cart_item, name="update_cart_item"),
    path("checkout/", views.checkout, name="checkout"),
    path("payment/success/", views.payment_success, name="payment_success"),
    path("payment/cancel/", views.payment_cancel, name="payment_cancel"),
    path("suivi/", views.order_tracking, name="order_tracking"),
]
