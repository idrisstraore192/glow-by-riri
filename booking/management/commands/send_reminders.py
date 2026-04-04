from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from booking.models import Appointment
import datetime


class Command(BaseCommand):
    help = 'Envoie un rappel par email aux clientes dont le RDV est demain'

    def handle(self, *args, **options):
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)

        appointments = Appointment.objects.filter(
            date=tomorrow,
            deposit_paid=True,
            reminder_sent=False,
        ).select_related('service')

        sent = 0
        for appt in appointments:
            if not appt.customer_email:
                continue
            try:
                send_mail(
                    subject="Rappel — Votre rendez-vous demain chez Glow by Riri",
                    message=(
                        f"Bonjour {appt.customer_name},\n\n"
                        f"Rappel : votre rendez-vous est demain à {appt.time.strftime('%H h %M')} "
                        f"pour {appt.service.name}.\n\n"
                        f"Date    : {appt.date.strftime('%d/%m/%Y')}\n"
                        f"Heure   : {appt.time.strftime('%H h %M')}\n"
                        f"Service : {appt.service.name}\n\n"
                        f"À demain !\n"
                        f"Riri — Glow by Riri"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[appt.customer_email],
                    fail_silently=False,
                )
                appt.reminder_sent = True
                appt.save(update_fields=['reminder_sent'])
                sent += 1
                self.stdout.write(f"Rappel envoyé à {appt.customer_email} pour le {appt.date}")
            except Exception as e:
                self.stderr.write(f"Erreur rappel RDV #{appt.id}: {e}")

        self.stdout.write(self.style.SUCCESS(f"{sent} rappel(s) envoyé(s)."))
