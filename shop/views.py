import json
import stripe
from django.db import models as django_models
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from .models import Product, ProductVariant, Order, OrderItem, TutorialVideo, PromoCode, WishlistItem, LaceVariant
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
    ).order_by('type_order', 'order', 'price')
    tutorial_videos = TutorialVideo.objects.select_related('product').all() if category == 'produits' else []
    return render(request, "shop/products.html", {"products": products, "current_category": category, "tutorial_videos": tutorial_videos})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    images = list(product.images.all())
    videos = list(product.videos.all())
    images_count = len(images)
    media_count = images_count + len(videos)

    # Nouveau système : combinaisons lace (type + taille + longueur + prix)
    lace_variants_json = json.dumps([
        {
            'type': lv.type_lace,
            'taille': lv.taille_lace,
            'longueur': lv.longueur,
            'price': '{:.2f}'.format(float(lv.price)),
            'photo_url': lv.photo_url or '',
            'video_url': lv.video_url or '',
            'stock': lv.stock,
        }
        for lv in product.lace_variants.all()
    ])

    # Ancien système : variantes simples (longueur uniquement, pour perruques sans lace)
    from collections import defaultdict
    variant_groups = []
    if not product.lace_variants.exists():
        vg = defaultdict(list)
        for v in product.variants.all():
            vg[v.variant_type].append(v)
        for vtype in ['longueur', 'lace', 'type_lace', 'densite', 'couleur']:
            if vtype in vg:
                label = dict(ProductVariant.TYPE_CHOICES).get(vtype, vtype)
                variant_groups.append({'type': vtype, 'label': label, 'options': vg[vtype]})

    related_products = Product.objects.filter(
        disponible=True, product_type=product.product_type
    ).exclude(pk=product.pk).order_by('?')[:4]

    return render(request, "shop/product_detail.html", {
        "product": product,
        "images": images,
        "images_count": images_count,
        "media_count": media_count,
        "videos": videos,
        "lace_variants_json": lace_variants_json,
        "variant_groups": variant_groups,
        "related_products": related_products,
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
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def respond(ok, msg):
        if is_ajax:
            return JsonResponse({'ok': ok, 'message': msg, 'cart_count': len(Cart(request))})
        if ok:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
        return redirect(request.META.get('HTTP_REFERER', 'products'))

    product = get_object_or_404(Product, id=product_id)
    if product.stock is not None and product.stock <= 0:
        return respond(False, f'{product.name} est en rupture de stock.')

    cart = Cart(request)
    with_installation = request.POST.get('with_installation') == '1'
    lace_type = request.POST.get('lace_type', '').strip()
    lace_taille = request.POST.get('lace_taille', '').strip()
    lace_longueur = request.POST.get('lace_longueur', '').strip()
    has_lace_variants = product.lace_variants.exists()

    if has_lace_variants:
        if not (lace_type and lace_taille and lace_longueur):
            return respond(False, 'Veuillez sélectionner le type, la taille et la longueur.')
        try:
            lv = LaceVariant.objects.get(product=product, type_lace=lace_type, taille_lace=lace_taille, longueur=lace_longueur)
            if lv.stock is not None and lv.stock <= 0:
                return respond(False, 'Cette variante est en rupture de stock.')
            cart.add(product, lace_variant=lv, with_installation=with_installation)
            type_display = dict(LaceVariant.TYPE_CHOICES).get(lace_type, lace_type)
            return respond(True, f'{product.name} — {type_display} · {lace_taille} · {lace_longueur} ajouté au panier ✦')
        except LaceVariant.DoesNotExist:
            return respond(False, 'Combinaison introuvable. Veuillez sélectionner une variante valide.')

    variant_id = request.POST.get('variant_id') or request.GET.get('variant_id')
    has_variants = product.variants.exists()
    if has_variants and not variant_id:
        return respond(False, 'Veuillez sélectionner une option avant d\'ajouter au panier.')
    variant = get_object_or_404(ProductVariant, id=variant_id, product=product) if variant_id else None
    if variant and variant.stock is not None and variant.stock <= 0:
        return respond(False, 'Cette option est en rupture de stock.')
    cart.add(product, variant=variant, with_installation=with_installation)
    label = f' — {variant.label}' if variant else ''
    pose = ' · Pose incluse (-5%)' if with_installation else ''
    return respond(True, f'{product.name}{label}{pose} ajouté au panier ✦')


def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    return redirect('cart')


def remove_cart_item(request, item_key):
    cart = Cart(request)
    try:
        product_id = int(item_key.split('_')[0])
        product = get_object_or_404(Product, id=product_id)
        cart.remove(product, item_key=item_key)
    except (ValueError, IndexError):
        pass
    return redirect('cart')


def update_cart_item(request, item_key):
    cart = Cart(request)
    try:
        product_id = int(item_key.split('_')[0])
        product = get_object_or_404(Product, id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        cart.update(product, quantity, item_key=item_key)
    except (ValueError, IndexError):
        pass
    return redirect('cart')


def cart_view(request):
    cart = Cart(request)
    promo_code = request.session.get('promo_code')
    promo_discount = 0
    promo_label = None
    if promo_code:
        try:
            promo = PromoCode.objects.get(code=promo_code)
            valid, _ = promo.is_valid()
            if valid:
                promo_discount = float(promo.discount_percent)
                promo_label = promo_code
        except PromoCode.DoesNotExist:
            del request.session['promo_code']
    total = cart.get_total()
    total_after_promo = round(total * (1 - promo_discount / 100), 2) if promo_discount else total
    return render(request, "shop/cart.html", {
        "cart": cart,
        "promo_discount": promo_discount,
        "promo_label": promo_label,
        "total_after_promo": total_after_promo,
    })


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('products')

    # Feature 10: validate prices server-side from DB
    line_items = []
    for item in cart:
        product = item['product']
        if product is None:
            continue
        # Re-fetch real price from DB
        try:
            db_product = Product.objects.get(pk=product.pk)
        except Product.DoesNotExist:
            continue
        real_price = db_product.final_price
        item_key = item.get('key', '')
        parts = item_key.split('_')
        with_pose = parts[-1] == 'pose'
        key_parts = parts[:-1] if with_pose else parts
        if len(key_parts) >= 2 and key_parts[1] == 'lv':
            # LaceVariant key: {product_id}_lv_{type}_{taille}_{longueur}[_pose]
            try:
                lv_type, lv_taille, lv_longueur = key_parts[2], key_parts[3], '_'.join(key_parts[4:])
                lv = LaceVariant.objects.get(product=db_product, type_lace=lv_type, taille_lace=lv_taille, longueur=lv_longueur)
                base = float(lv.price)
                if db_product.discount_percent and db_product.discount_percent > 0:
                    base = round(base * (1 - float(db_product.discount_percent) / 100), 2)
                real_price = base
            except (IndexError, LaceVariant.DoesNotExist):
                pass
        elif len(key_parts) >= 2:
            # ProductVariant key: {product_id}_{variant_id}[_pose]
            try:
                variant = ProductVariant.objects.get(pk=int(key_parts[1]))
                if variant.price:
                    base = float(variant.price)
                    if db_product.discount_percent and db_product.discount_percent > 0:
                        base = round(base * (1 - float(db_product.discount_percent) / 100), 2)
                    real_price = base
            except (ValueError, ProductVariant.DoesNotExist):
                pass
        if with_pose:
            real_price = round(real_price * 0.95, 2)
        line_items.append({
            'price_data': {
                'currency': 'cad',
                'product_data': {'name': item['product'].name},
                'unit_amount': int(real_price * 100),
            },
            'quantity': item['quantity'],
        })

    # Feature 7: apply promo code discount via Stripe coupon
    discounts = []
    promo_code = request.session.get('promo_code')
    if promo_code:
        try:
            promo = PromoCode.objects.get(code=promo_code)
            valid, _ = promo.is_valid()
            if valid:
                coupon = stripe.Coupon.create(
                    percent_off=float(promo.discount_percent),
                    duration='once',
                )
                discounts = [{'coupon': coupon.id}]
        except PromoCode.DoesNotExist:
            pass

    session_kwargs = dict(
        payment_method_types=['card', 'klarna'],
        line_items=line_items,
        mode='payment',
        metadata={'type': 'order'},
        shipping_address_collection={'allowed_countries': ['CA']},
        shipping_options=[
            {
                'shipping_rate_data': {
                    'type': 'fixed_amount',
                    'fixed_amount': {'amount': 0, 'currency': 'cad'},
                    'display_name': 'Remise en main propre — Trois-Rivières',
                },
            },
            {
                'shipping_rate_data': {
                    'type': 'fixed_amount',
                    'fixed_amount': {'amount': 500, 'currency': 'cad'},
                    'display_name': 'Livraison — Trois-Rivières',
                    'delivery_estimate': {
                        'minimum': {'unit': 'business_day', 'value': 1},
                        'maximum': {'unit': 'business_day', 'value': 2},
                    },
                },
            },
            {
                'shipping_rate_data': {
                    'type': 'fixed_amount',
                    'fixed_amount': {'amount': 2100, 'currency': 'cad'},
                    'display_name': 'Livraison — Partout au Canada',
                    'delivery_estimate': {
                        'minimum': {'unit': 'business_day', 'value': 3},
                        'maximum': {'unit': 'business_day', 'value': 7},
                    },
                },
            },
        ],
        success_url=SITE_URL + '/shop/payment/success/?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=SITE_URL + '/shop/payment/cancel/',
    )
    if discounts:
        session_kwargs['discounts'] = discounts

    session = stripe.checkout.Session.create(**session_kwargs)
    return redirect(session.url, code=303)


def payment_success(request):
    session_id = request.GET.get('session_id')
    cart = Cart(request)
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id, expand=['shipping_cost.shipping_rate'])
            shipping_name = ''
            if session.shipping_cost and session.shipping_cost.shipping_rate:
                shipping_name = session.shipping_cost.shipping_rate.display_name or ''
            is_pickup = 'main propre' in shipping_name.lower()
            if is_pickup:
                shipping_address = 'Remise en main propre'
            else:
                addr = session.shipping_details.address if session.shipping_details else None
                shipping_address = ''
                if addr:
                    parts = [addr.line1, addr.line2, addr.city, addr.state, addr.postal_code, addr.country]
                    shipping_address = ', '.join(p for p in parts if p)
            order = Order.objects.create(
                customer_name=session.customer_details.name or "Cliente",
                customer_email=session.customer_details.email or "",
                total=session.amount_total / 100,
                stripe_session_id=session_id,
                shipping_address=shipping_address,
                paid=True,
            )
            items_list = list(cart)
            for item in items_list:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    product_name=item.get('product_name') or (item['product'].name if item['product'] else 'Produit supprimé'),
                    price=item['price'],
                    quantity=item['quantity'],
                )
                # Feature 13: decrement stock
                if item['product'] and item['product'].stock is not None:
                    Product.objects.filter(pk=item['product'].pk, stock__gt=0).update(
                        stock=django_models.F('stock') - item['quantity']
                    )
                    updated = Product.objects.filter(pk=item['product'].pk, stock=0).first()
                    if updated:
                        try:
                            send_mail(
                                subject=f"Rupture de stock — {updated.name}",
                                message=(
                                    f"Le stock du produit suivant vient d'atteindre 0 suite à une commande :\n\n"
                                    f"Produit : {updated.name}\n\n"
                                    f"Pense à réapprovisionner ou à désactiver le produit.\n\nGlow by Riri"
                                ),
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[settings.ADMIN_EMAIL],
                                fail_silently=True,
                            )
                        except Exception:
                            pass
            # Feature 7: increment promo code uses
            promo_code = request.session.get('promo_code')
            if promo_code:
                try:
                    PromoCode.objects.filter(code=promo_code).update(
                        uses_count=django_models.F('uses_count') + 1
                    )
                    del request.session['promo_code']
                except Exception:
                    pass
            cart.clear()
            _send_order_emails(order, items_list)
        except Exception as e:
            logger.error(f"payment_success order creation error: {e}")
    return render(request, "shop/payment_success.html")


def _generate_invoice_pdf(order):
    """Returns a BytesIO with the invoice PDF, or None if ReportLab is unavailable."""
    try:
        import io
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        pink = colors.HexColor('#f8d0e8')
        dark = colors.HexColor('#1a1a1a')

        title_style = ParagraphStyle('title', parent=styles['Heading1'],
                                     textColor=dark, fontSize=20, spaceAfter=4)
        normal = styles['Normal']

        elements = []
        elements.append(Paragraph("Glow by Riri", title_style))
        elements.append(Paragraph("glowbyririi@gmail.com — glowbyriri.up.railway.app", normal))
        elements.append(Spacer(1, 0.4*cm))
        elements.append(Paragraph(f"<b>Facture #{order.id}</b>", styles['Heading2']))
        elements.append(Paragraph(f"Date : {order.created_at.strftime('%d/%m/%Y')}", normal))
        elements.append(Paragraph(f"Cliente : {order.customer_name} ({order.customer_email})", normal))
        elements.append(Spacer(1, 0.6*cm))

        data = [['Article', 'Prix unitaire', 'Qté', 'Total']]
        for item in order.items.all():
            data.append([
                item.product_name,
                f"{float(item.price):.2f} $",
                str(item.quantity),
                f"{float(item.price) * item.quantity:.2f} $",
            ])
        data.append(['', '', 'TOTAL', f"{float(order.total):.2f} $"])

        table = Table(data, colWidths=[9*cm, 3*cm, 2*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), pink),
            ('TEXTCOLOR', (0, 0), (-1, 0), dark),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -1), (-1, -1), 1, dark),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#fdf6fb')]),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph("Merci pour votre confiance — Glow by Riri", normal))

        doc.build(elements)
        buffer.seek(0)
        return buffer
    except Exception:
        return None


def _send_order_emails(order, items):
    def _item_name(item):
        if item.get('product'):
            return item['product'].name
        return item.get('product_name') or 'Article'

    lines = '\n'.join(
        f"  • {_item_name(item)}"
        + (f" — {item['label']}" if item.get('label') else '')
        + f"  x{item['quantity']}  {float(item['price']):.2f} $"
        for item in items
    )
    total = f"{float(order.total):.2f} $"

    is_pickup = order.shipping_address == 'Remise en main propre'
    livraison_msg = (
        "Tu peux venir récupérer ta commande en main propre à Trois-Rivières. Riri te contactera pour convenir d'un moment."
        if is_pickup else
        "Ta commande est en cours de traitement. Tu recevras un message dès qu'elle est expédiée."
    )

    if order.customer_email:
        client_msg = (
            f"Bonjour {order.customer_name},\n\n"
            f"Merci pour ta commande chez Glow by Riri !\n\n"
            f"Voici ton récapitulatif :\n{lines}\n\n"
            f"Total payé : {total}\n\n"
            f"{livraison_msg}\n\n"
            f"Facture : {SITE_URL}/shop/order/{order.id}/invoice.pdf/?email={order.customer_email}\n\n"
            f"Des questions ? Écris-nous à glowbyririi@gmail.com\n\n"
            f"À bientôt,\nRiri — Glow by Riri"
        )
        try:
            html_message = render_to_string('emails/order_confirmation.html', {
                'order': order,
                'items': items,
                'is_pickup': is_pickup,
                'livraison_msg': livraison_msg,
                'site_url': SITE_URL,
            })
            msg = EmailMultiAlternatives(
                subject=f"Confirmation de ta commande #{order.id} — Glow by Riri",
                body=client_msg,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.customer_email],
            )
            msg.attach_alternative(html_message, "text/html")
            pdf_buffer = _generate_invoice_pdf(order)
            if pdf_buffer:
                msg.attach(f"facture-{order.id}.pdf", pdf_buffer.read(), 'application/pdf')
            msg.send(fail_silently=True)
        except Exception:
            try:
                send_mail(
                    subject=f"Confirmation de ta commande #{order.id} — Glow by Riri",
                    message=client_msg,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.customer_email],
                    fail_silently=True,
                )
            except Exception:
                pass

    livraison_admin = "REMISE EN MAIN PROPRE — à contacter pour convenir d'un moment." if is_pickup else f"Livraison\nAdresse : {order.shipping_address}"
    admin_msg = (
        f"Nouvelle commande #{order.id}\n\n"
        f"Cliente : {order.customer_name} ({order.customer_email})\n\n"
        f"Articles :\n{lines}\n\n"
        f"Total : {total}\n\n"
        f"{livraison_admin}\n"
    )
    try:
        send_mail(
            subject=f"Nouvelle commande #{order.id} — {total}",
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


def checkout_review(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('products')
    promo_code = request.session.get('promo_code')
    promo_discount = 0
    promo_label = None
    if promo_code:
        try:
            promo = PromoCode.objects.get(code=promo_code)
            valid, _ = promo.is_valid()
            if valid:
                promo_discount = float(promo.discount_percent)
                promo_label = promo_code
        except PromoCode.DoesNotExist:
            pass
    total = cart.get_total()
    total_after_promo = round(total * (1 - promo_discount / 100), 2) if promo_discount else total
    return render(request, "shop/checkout_review.html", {
        "cart": cart,
        "promo_discount": promo_discount,
        "promo_label": promo_label,
        "total_after_promo": total_after_promo,
    })


# ── Feature 4: Stripe Webhook ─────────────────────────────────────────────────
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        meta = session.get('metadata') or {}
        event_type = meta.get('type', '')

        if event_type == 'order':
            # Only create order if not already created (avoid duplicate with payment_success)
            session_id = session['id']
            if not Order.objects.filter(stripe_session_id=session_id).exists():
                try:
                    full_session = stripe.checkout.Session.retrieve(session_id, expand=['shipping_cost.shipping_rate'])
                    shipping_name = ''
                    if full_session.shipping_cost and full_session.shipping_cost.shipping_rate:
                        shipping_name = full_session.shipping_cost.shipping_rate.display_name or ''
                    is_pickup = 'main propre' in shipping_name.lower()
                    if is_pickup:
                        shipping_address = 'Remise en main propre'
                    else:
                        addr = full_session.shipping_details.address if full_session.shipping_details else None
                        shipping_address = ''
                        if addr:
                            parts = [addr.line1, addr.line2, addr.city, addr.state, addr.postal_code, addr.country]
                            shipping_address = ', '.join(p for p in parts if p)
                    order = Order.objects.create(
                        customer_name=full_session.customer_details.name or "Cliente",
                        customer_email=full_session.customer_details.email or "",
                        total=full_session.amount_total / 100,
                        stripe_session_id=session_id,
                        shipping_address=shipping_address,
                        paid=True,
                    )
                    line_items_response = stripe.checkout.Session.list_line_items(session_id)
                    for li in line_items_response.data:
                        OrderItem.objects.create(
                            order=order,
                            product=None,
                            product_name=li.description or 'Article',
                            price=li.amount_total / 100 / (li.quantity or 1),
                            quantity=li.quantity or 1,
                        )
                    items_for_email = [
                        {
                            'product': oi.product,
                            'product_name': oi.product_name,
                            'label': None,
                            'quantity': oi.quantity,
                            'price': str(oi.price),
                        }
                        for oi in order.items.all()
                    ]
                    _send_order_emails(order, items_for_email)
                except Exception as e:
                    logger.error(f"Webhook order creation error: {e}")

        elif event_type == 'deposit':
            appt_id = meta.get('appt_id')
            if appt_id:
                try:
                    from booking.models import Appointment
                    appt = Appointment.objects.get(id=appt_id, deposit_paid=False)
                    appt.deposit_paid = True
                    appt.save(update_fields=['deposit_paid'])
                    if appt.slot_id:
                        appt.slot.is_booked = True
                        appt.slot.save()
                except Exception as e:
                    logger.error(f"Webhook deposit confirmation error: {e}")

    return HttpResponse(status=200)


# ── Feature 7: Apply Promo Code (AJAX) ───────────────────────────────────────
def apply_promo(request):
    if request.method != 'POST':
        return JsonResponse({'valid': False, 'message': 'Méthode non autorisée.'})
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip().upper()
    except (json.JSONDecodeError, AttributeError):
        code = request.POST.get('code', '').strip().upper()

    if not code:
        return JsonResponse({'valid': False, 'message': 'Veuillez entrer un code promo.'})

    try:
        promo = PromoCode.objects.get(code=code)
    except PromoCode.DoesNotExist:
        return JsonResponse({'valid': False, 'message': 'Code promo invalide.'})

    valid, msg = promo.is_valid()
    if not valid:
        return JsonResponse({'valid': False, 'message': msg})

    request.session['promo_code'] = promo.code
    return JsonResponse({
        'valid': True,
        'discount': float(promo.discount_percent),
        'message': f'Code "{promo.code}" appliqué — {promo.discount_percent:.0f}% de réduction !',
    })


# ── Feature 9: Invoice PDF ────────────────────────────────────────────────────
def invoice_pdf(request, order_id):
    email = request.GET.get('email', '').strip()
    order = get_object_or_404(Order, id=order_id, paid=True)
    if email.lower() != order.customer_email.lower():
        return HttpResponse("Accès refusé.", status=403)

    buffer = _generate_invoice_pdf(order)
    if buffer is None:
        return HttpResponse("ReportLab non installé.", status=500)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="facture-{order.id}.pdf"'
    return response


# ── Feature 11: Mon compte ────────────────────────────────────────────────────
def mon_compte(request):
    orders = None
    appointments = None
    email = request.GET.get('email', '').strip()
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
    if email:
        orders = Order.objects.filter(customer_email__iexact=email, paid=True).prefetch_related('items').order_by('-created_at')
        try:
            from booking.models import Appointment
            appointments = Appointment.objects.filter(customer_email__iexact=email).select_related('service').order_by('-date', '-time')
        except Exception:
            appointments = []
    return render(request, 'shop/mon_compte.html', {'orders': orders, 'appointments': appointments, 'email': email})


# ── Feature 12: Wishlist ──────────────────────────────────────────────────────
def wishlist_toggle(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)
    product = get_object_or_404(Product, id=product_id)
    if not request.session.session_key:
        request.session.create()
    sk = request.session.session_key
    obj, created = WishlistItem.objects.get_or_create(session_key=sk, product=product)
    if not created:
        obj.delete()
        return JsonResponse({'in_wishlist': False, 'message': 'Retiré des favoris.'})
    return JsonResponse({'in_wishlist': True, 'message': 'Ajouté aux favoris !'})


def wishlist_view(request):
    if not request.session.session_key:
        request.session.create()
    sk = request.session.session_key
    items = WishlistItem.objects.filter(session_key=sk).select_related('product').order_by('-added_at')
    return render(request, 'shop/wishlist.html', {'items': items})


# ── Feature 14: product detail by slug ───────────────────────────────────────
def product_detail_slug(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return product_detail(request, product.id)
