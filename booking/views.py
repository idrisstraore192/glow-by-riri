from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import AppointmentForm
from .models import Service
from reviews.models import Review
from reviews.forms import ReviewForm

def booking_page(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appt = form.save()
            messages.success(request, 'Votre rendez-vous a été confirmé !')
            try:
                send_mail(
                    subject=f"📅 Nouveau rendez-vous — {appt.customer_name}",
                    message=(
                        f"Tu as un nouveau rendez-vous ✦\n\n"
                        f"Cliente     : {appt.customer_name}\n"
                        f"Service     : {appt.service.name}\n"
                        f"Prix        : {appt.service.final_price} $\n"
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
            return redirect('booking_success')
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


def booking_success(request):
    return render(request, 'booking/success.html')
