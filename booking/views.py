from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import AppointmentForm


def booking_page(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre rendez-vous a été confirmé !')
            return redirect('booking_success')
    else:
        form = AppointmentForm()
    return render(request, 'booking/booking.html', {'form': form})


def booking_success(request):
    return render(request, 'booking/success.html')
