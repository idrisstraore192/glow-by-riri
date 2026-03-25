import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from .forms import AppointmentForm
from .models import Service, Appointment
from reviews.models import Review
from reviews.forms import ReviewForm

stripe.api_key = settings.STRIPE_SECRET_KEY
SITE_URL = "https://glowbyriri.up.railway.app"
DEPOSIT_AMOUNT = 2000  # 20.00 $ en centimes


def booking_page(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appt = form.save(commit=False)
            slot = form.cleaned_data['slot']
            appt.date = slot.date
            appt.time = slot.time
            appt.deposit_paid = False
            appt.save()

            try:
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'cad',
                            'product_data': {
                                'name': f'Acompte — {appt.service.name}',
                                'description': f'Rendez-vous le {appt.date.strftime("%d/%m/%Y")} à {appt.time.strftime("%H:%M")} · Reste à payer sur place : {appt.service.final_price - 20:.2f} $',
                            },
                            'unit_amount': DEPOSIT_AMOUNT,
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    customer_email=appt.customer_email or None,
                    success_url=SITE_URL + f'/booking/deposit/success/?session_id={{CHECKOUT_SESSION_ID}}&appt_id={appt.id}',
                    cancel_url=SITE_URL + f'/booking/deposit/cancel/?appt_id={appt.id}',
                )
                appt.stripe_session_id = session.id
                appt.save()
                return redirect(session.url, code=303)
            except Exception:
                appt.delete()
                return render(request, 'booking/booking.html', {
                    'form': form,
                    'services': Service.objects.all().order_by('price'),
                    'reviews': Review.objects.filter(approved=True)[:6],
                    'review_form': ReviewForm(),
                    'categories': Service.CATEGORY_CHOICES,
                    'payment_error': True,
                })
    else:
        form = AppointmentForm()

    category = request.GET.get('category', '')
    price_range = request.GET.get('price', '')

    services = Service.objects.all().order_by('price')
    if category:
        services = services.filter(category=category)
    if price_range == '0-50':
        services = services.filter(price__lte=50)
    elif price_range == '50-100':
        services = services.filter(price__gt=50, price__lte=100)
    elif price_range == '100+':
        services = services.filter(price__gt=100)

    sort = request.GET.get('sort', '')
    if sort == 'asc':
        services = services.order_by('price')
    elif sort == 'desc':
        services = services.order_by('-price')

    reviews = Review.objects.filter(approved=True)[:6]
    review_form = ReviewForm()
    submitted = request.GET.get('avis') == 'merci'
    return render(request, 'booking/booking.html', {
        'form': form,
        'services': services,
        'reviews': reviews,
        'review_form': review_form,
        'submitted': submitted,
        'active_category': category,
        'active_price': price_range,
        'active_sort': sort,
        'categories': Service.CATEGORY_CHOICES,
    })


def booking_deposit_success(request):
    session_id = request.GET.get('session_id')
    appt_id = request.GET.get('appt_id')
    appt = get_object_or_404(Appointment, id=appt_id)

    if session_id and not appt.deposit_paid:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                appt.deposit_paid = True
                appt.stripe_session_id = session_id
                appt.save()
                if appt.slot_id:
                    appt.slot.is_booked = True
                    appt.slot.save()

                # Email à Riri
                try:
                    send_mail(
                        subject=f"📅 Nouveau rendez-vous — {appt.customer_name}",
                        message=(
                            f"Tu as un nouveau rendez-vous ✦\n\n"
                            f"Cliente     : {appt.customer_name}\n"
                            f"Email       : {appt.customer_email}\n"
                            f"Service     : {appt.service.name}\n"
                            f"Prix total  : {appt.service.final_price} $\n"
                            f"Acompte     : 20,00 $ ✓ payé\n"
                            f"Reste à payer : {appt.service.final_price - 20:.2f} $\n"
                            f"Date        : {appt.date.strftime('%A %d %B %Y')}\n"
                            f"Heure       : {appt.time.strftime('%H h %M')}\n\n"
                            f"Consulte tous tes rendez-vous ici :\n"
                            f"https://glowbyriri.up.railway.app/admin/booking/appointment/\n\n"
                            f"Glow by Riri 💕"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.ADMIN_EMAIL],
                        fail_silently=True,
                    )
                except Exception:
                    pass

                # Email de confirmation à la cliente
                if appt.customer_email:
                    try:
                        send_mail(
                            subject="✦ Votre rendez-vous est confirmé — Glow by Riri",
                            message=(
                                f"Bonjour {appt.customer_name} ✦\n\n"
                                f"Votre rendez-vous est confirmé !\n\n"
                                f"Service     : {appt.service.name}\n"
                                f"Date        : {appt.date.strftime('%A %d %B %Y')}\n"
                                f"Heure       : {appt.time.strftime('%H h %M')}\n"
                                f"Acompte payé : 20,00 $\n"
                                f"Reste à régler sur place : {appt.service.final_price - 20:.2f} $\n\n"
                                f"À très bientôt,\n"
                                f"Riri — Glow by Riri 💕"
                            ),
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[appt.customer_email],
                            fail_silently=True,
                        )
                    except Exception:
                        pass
        except Exception:
            pass

    remainder = round(appt.service.final_price - 20, 2)
    return render(request, 'booking/success.html', {'appt': appt, 'remainder': remainder})


def booking_deposit_cancel(request):
    appt_id = request.GET.get('appt_id')
    if appt_id:
        try:
            appt = Appointment.objects.get(id=appt_id, deposit_paid=False)
            appt.delete()
        except Appointment.DoesNotExist:
            pass
    return render(request, 'booking/deposit_cancel.html')


def booking_success(request):
    return render(request, 'booking/success.html')
