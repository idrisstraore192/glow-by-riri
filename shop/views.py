import json
import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from .models import Product, ProductVariant, Order, OrderItem, TutorialVideo
from .cart import Cart

stripe.api_key = settings.STRIPE_SECRET_KEY
SITE_URL = "https://glowbyriri.up.railway.app"


def product_list(request):
    from django.db.models import Case, When, IntegerField, Value
    category = request.GET.get('category')
    qs = Product.objects.filter(disponible=True)
    if category == 'produits':
        qs = qs.filter(product_type='produit')
    elif category == 'perruques':
        qs = qs.filter(product_type='perruque')
    elif category == 'bundles':
        qs = qs.filter(product_type__in=['bundle', 'lace'])
    elif category:
        qs = qs.filter(category=category)
    products = qs.annotate(
        type_order=Case(
            When(product_type='produit',  then=Value(0)),
            When(product_type='perruque', then=Value(1)),
            When(product_type='lace',     then=Value(2)),
            When(product_type='bundle',   then=Value(3)),
            default=Value(3),
            output_field=IntegerField(),
        )
    ).order_by('type_order', 'price')
    tutorial_videos = TutorialVideo.objects.select_related('product').all() if category == 'produits' else []
    return render(request, "shop/products.html", {"products": products, "current_category": category, "tutorial_videos": tutorial_videos})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    images = product.images.all()
    from collections import defaultdict
    variant_groups = defaultdict(list)
    for v in product.variants.all():
        variant_groups[v.variant_type].append(v)
    ordered_groups = []
    for vtype in ['longueur', 'densite']:
        if vtype in variant_groups:
            label = dict(product.variants.model.TYPE_CHOICES).get(vtype, vtype)
            ordered_groups.append({'type': vtype, 'label': label, 'options': variant_groups[vtype]})
    videos = list(product.videos.all())
    images_count = len(images)
    media_count = images_count + len(videos)

    lace_json = 'null'
    if product.product_type == 'perruque':
        lace_products = Product.objects.filter(product_type='lace').prefetch_related('variants')
        lace_list = []
        for lp in lace_products:
            variants = [
                {'id': v.id, 'label': v.label, 'price': '{:.2f}'.format(float(v.price))}
                for v in lp.variants.filter(variant_type='longueur')
            ]
            lace_list.append({'id': lp.id, 'name': lp.name, 'variants': variants})
        lace_json = json.dumps(lace_list)

    return render(request, "shop/product_detail.html", {
        "product": product,
        "images": images,
        "images_count": images_count,
        "media_count": media_count,
        "videos": videos,
        "variant_groups": ordered_groups,
        "lace_json": lace_json,
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

    lace_variant_id = request.POST.get('lace_variant_id')
    if lace_variant_id:
        try:
            lace_variant = ProductVariant.objects.select_related('product').get(id=lace_variant_id)
            lace_product = lace_variant.product
            cart.add(lace_product, variant=lace_variant)
            messages.success(request, f'{lace_product.name} — {lace_variant.label} ajouté au panier ✦')
        except ProductVariant.DoesNotExist:
            pass

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
            items_list = list(cart)
            for item in items_list:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    product_name=item['product'].name,
                    price=item['price'],
                    quantity=item['quantity'],
                )
            cart.clear()
            _send_order_emails(order, items_list)
        except Exception:
            pass
    return render(request, "shop/payment_success.html")


def _send_order_emails(order, items):
    lines = '\n'.join(
        f"  • {item['product'].name}"
        + (f" — {item['label']}" if item.get('label') else '')
        + f"  x{item['quantity']}  {float(item['price']):.2f} $"
        for item in items
    )
    total = f"{float(order.total):.2f} $"

    if order.customer_email:
        client_msg = f"""Bonjour {order.customer_name} ✦

Merci pour ta commande chez Glow by Riri ! 🌸

Voici ton récapitulatif :
{lines}

Total payé : {total}

Ta commande est en cours de traitement. Tu recevras un message dès qu'elle est expédiée.

Des questions ? Écris-nous à glowbyririi@gmail.com

À bientôt,
Riri — Glow by Riri 💕
"""
        try:
            send_mail(
                subject=f"✦ Confirmation de ta commande #{order.id} — Glow by Riri",
                message=client_msg,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.customer_email],
                fail_silently=True,
            )
        except Exception:
            pass

    admin_msg = f"""Nouvelle commande #{order.id} 🛍️

Cliente : {order.customer_name} ({order.customer_email})

Articles :
{lines}

Total : {total}
"""
    try:
        send_mail(
            subject=f"🛍️ Nouvelle commande #{order.id} — {total}",
            message=admin_msg,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=True,
        )
    except Exception:
        pass


def payment_cancel(request):
    return render(request, "shop/payment_cancel.html")


def order_tracking(request):
    orders = None
    email = request.GET.get('email', '').strip()
    if email:
        orders = Order.objects.filter(customer_email__iexact=email, paid=True).prefetch_related('items').order_by('-created_at')
    return render(request, "shop/order_tracking.html", {"orders": orders, "email": email})
