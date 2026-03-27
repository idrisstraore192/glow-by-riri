from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from booking.models import Appointment
import datetime


class Command(BaseCommand):
    help = 'Envoie un rappel par email aux clientes 1h avant leur rendez-vous'

    def handle(self, *args, **options):
        now = timezone.localtime()
        window_start = (now + datetime.timedelta(minutes=55)).time()
        window_end   = (now + datetime.timedelta(minutes=70)).time()
        today = now.date()

        appointments = Appointment.objects.filter(
            date=today,
            deposit_paid=True,
            reminder_sent=False,
            time__gte=window_start,
            time__lte=window_end,
        )

        for appt in appointments:
            if not appt.customer_email:
                continue
            try:
                send_mail(
                    subject="⏰ Rappel — Ton rendez-vous chez Glow by Riri dans 1h",
                    message=f"""Bonjour {appt.customer_name} ✦

C'est ton rappel ! Ton rendez-vous est dans environ 1 heure.

Service  : {appt.service.name}
Date     : {appt.date.strftime('%d/%m/%Y')}
Heure    : {appt.time.strftime('%H h %M')}

À tout à l'heure !
Riri — Glow by Riri 💕
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[appt.customer_email],
                    fail_silently=False,
                )
                appt.reminder_sent = True
                appt.save(update_fields=['reminder_sent'])
                self.stdout.write(f"Rappel envoyé à {appt.customer_email}")
            except Exception as e:
                self.stderr.write(f"Erreur rappel {appt.id}: {e}")
