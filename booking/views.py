from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import AppointmentForm
from .models import Service
from reviews.models import Review
from reviews.forms import ReviewForm

def booking_page(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre rendez-vous a été confirmé !')
            return redirect('booking_success')
    else:
        form = AppointmentForm()
    services = Service.objects.all()
    reviews = Review.objects.filter(approved=True)[:6]
    review_form = ReviewForm()
    submitted = request.GET.get('avis') == 'merci'
    return render(request, 'booking/booking.html', {
        'form': form,
        'services': services,
        'reviews': reviews,
        'review_form': review_form,
        'submitted': submitted,
    })


def booking_success(request):
    return render(request, 'booking/success.html')
