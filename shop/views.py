import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from .models import Product, ProductVariant, Order, OrderItem
from .cart import Cart

stripe.api_key = settings.STRIPE_SECRET_KEY
SITE_URL = "https://web-production-ff3c4.up.railway.app"


def product_list(request):
    category = request.GET.get('category')
    if category:
        # Perruques d'abord, puis laces — chaque groupe par prix croissant
        products = Product.objects.filter(category=category).order_by('product_type', 'price')
    else:
        products = Product.objects.all().order_by('category', 'product_type', 'price')
    return render(request, "shop/products.html", {"products": products, "current_category": category})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    images = product.images.all()
    # Grouper les variantes par type
    from collections import defaultdict
    variant_groups = defaultdict(list)
    for v in product.variants.all():
        variant_groups[v.variant_type].append(v)
    # Ordre d'affichage
    ordered_groups = []
    for vtype in ['longueur', 'fermeture', 'densite']:
        if vtype in variant_groups:
            label = dict(product.variants.model.TYPE_CHOICES).get(vtype, vtype)
            ordered_groups.append({'type': vtype, 'label': label, 'options': variant_groups[vtype]})
    videos = list(product.videos.all())
    images_count = len(images)
    media_count = images_count + len(videos)
    return render(request, "shop/product_detail.html", {
        "product": product,
        "images": images,
        "images_count": images_count,
        "media_count": media_count,
        "videos": videos,
        "variant_groups": ordered_groups,
    })


def update_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = 1
    cart.update(product, quantity)
    return redirect('cart')


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    variant_id = request.POST.get('variant_id') or request.GET.get('variant_id')
    variant = get_object_or_404(ProductVariant, id=variant_id, product=product) if variant_id else None
    with_installation = request.POST.get('with_installation') == '1'
    cart.add(product, variant=variant, with_installation=with_installation)
    label = f' — {variant.label}' if variant else ''
    promo = ' (-5% pose incluse)' if with_installation else ''
    messages.success(request, f'{product.name}{label}{promo} ajouté au panier ✦')
    return redirect(request.META.get('HTTP_REFERER', 'products'))


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
