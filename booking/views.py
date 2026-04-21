import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .forms import AppointmentForm
from .models import Service, Appointment
from reviews.models import Review
from reviews.forms import ReviewForm

stripe.api_key = settings.STRIPE_SECRET_KEY
SITE_URL = "https://glowbyriri.up.railway.app"


def booking_page(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appt = form.save(commit=False)
            slot = form.cleaned_data['slot']
            appt.date = slot.date
            appt.time = slot.time
            appt.deposit_paid = False
            nattes_val = form.cleaned_data.get('nattes_deja_faites')
            if appt.service.nattes_requises and nattes_val == 'oui':
                appt.nattes_deja_faites = True
            elif appt.service.nattes_requises and nattes_val == 'non':
                appt.nattes_deja_faites = False
            else:
                appt.nattes_deja_faites = None
            appt.save()

            try:
                nattes_note = ''
                if appt.service.nattes_requises and appt.nattes_deja_faites is False:
                    nattes_note = ' · Nattes incluses (+10 $ CAD)'
                elif appt.service.nattes_requises and appt.nattes_deja_faites is True:
                    nattes_note = ' · Nattes déjà faites'
                remainder = round(appt.total_price - float(appt.service.deposit_amount), 2)
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'cad',
                            'product_data': {
                                'name': f'Acompte — {appt.service.name}',
                                'description': f'Rendez-vous le {appt.date.strftime("%d/%m/%Y")} à {appt.time.strftime("%H:%M")}{nattes_note} · Reste à payer sur place : {remainder:.2f} $',
                            },
                            'unit_amount': int(appt.service.deposit_amount * 100),
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    customer_email=appt.customer_email or None,
                    metadata={'type': 'deposit', 'appt_id': str(appt.id)},
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
    services_nattes = list(Service.objects.filter(nattes_requises=True).values_list('id', flat=True))
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
        'services_nattes_ids': services_nattes,
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
                    _nattes_line = ''
                    if appt.service.nattes_requises:
                        if appt.nattes_deja_faites is True:
                            _nattes_line = f"Nattes       : Déjà faites (pas de supplément)\n"
                        elif appt.nattes_deja_faites is False:
                            _nattes_line = f"Nattes       : À faire sur place (+10 $ CAD inclus dans le total)\n"
                    send_mail(
                        subject=f"📅 Nouveau rendez-vous — {appt.customer_name}",
                        message=(
                            f"Tu as un nouveau rendez-vous ✦\n\n"
                            f"Cliente     : {appt.customer_name}\n"
                            f"Email       : {appt.customer_email}\n"
                            f"Service     : {appt.service.name}\n"
                            f"{_nattes_line}"
                            f"Prix total  : {appt.total_price} $\n"
                            f"Acompte     : {float(appt.service.deposit_amount):.2f} $ ✓ payé\n"
                            f"Reste à payer : {appt.total_price - float(appt.service.deposit_amount):.2f} $\n"
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
                        _remainder = round(appt.total_price - float(appt.service.deposit_amount), 2)
                        plain_confirm = (
                            f"Bonjour {appt.customer_name},\n\n"
                            f"Votre rendez-vous est confirmé !\n\n"
                            f"Service     : {appt.service.name}\n"
                            f"Date        : {appt.date.strftime('%A %d %B %Y')}\n"
                            f"Heure       : {appt.time.strftime('%H h %M')}\n"
                            f"Acompte payé : {float(appt.service.deposit_amount):.2f} $\n"
                            f"Reste à régler sur place : {_remainder:.2f} $\n\n"
                            f"À très bientôt,\nRiri — Glow by Riri"
                        )
                        try:
                            html_confirm = render_to_string('emails/appointment_confirmation.html', {
                                'appt': appt,
                                'remainder': _remainder,
                            })
                            confirm_msg = EmailMultiAlternatives(
                                subject="Votre rendez-vous est confirmé — Glow by Riri",
                                body=plain_confirm,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                to=[appt.customer_email],
                            )
                            confirm_msg.attach_alternative(html_confirm, "text/html")
                            confirm_msg.send(fail_silently=True)
                        except Exception:
                            send_mail(
                                subject="Votre rendez-vous est confirmé — Glow by Riri",
                                message=plain_confirm,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[appt.customer_email],
                                fail_silently=True,
                            )
                    except Exception:
                        pass
        except Exception:
            pass

    remainder = round(appt.total_price - float(appt.service.deposit_amount), 2)
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
