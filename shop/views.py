import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .models import Product, Order, OrderItem
from .cart import Cart

stripe.api_key = settings.STRIPE_SECRET_KEY
SITE_URL = "https://web-production-ff3c4.up.railway.app"


def product_list(request):
    products = Product.objects.all()
    return render(request, "shop/products.html", {"products": products})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.add(product)
    return redirect('cart')


def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    return redirect('cart')


def cart_view(request):
    cart = Cart(request)
    return render(request, "shop/cart.html", {"cart": cart})


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('products')

    line_items = []
    for item in cart:
        line_items.append({
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': item['product'].name},
                'unit_amount': int(float(item['price']) * 100),
            },
            'quantity': item['quantity'],
        })

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=SITE_URL + '/shop/payment/success/?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=SITE_URL + '/shop/payment/cancel/',
    )
    return redirect(session.url, code=303)


def payment_success(request):
    session_id = request.GET.get('session_id')
    cart = Cart(request)
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            order = Order.objects.create(
                customer_name=session.customer_details.name or "Cliente",
                customer_email=session.customer_details.email or "",
                total=session.amount_total / 100,
                stripe_session_id=session_id,
                paid=True,
            )
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    product_name=item['product'].name,
                    price=item['price'],
                    quantity=item['quantity'],
                )
            cart.clear()
        except Exception:
            pass
    return render(request, "shop/payment_success.html")


def payment_cancel(request):
    return render(request, "shop/payment_cancel.html")
