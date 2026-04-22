from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Envoie un email de test pour vérifier la config SMTP'

    def handle(self, *args, **kwargs):
        self.stdout.write('Envoi de l\'email de test...')
        try:
            send_mail(
                subject='Test email — Glow by Riri',
                message='Si tu reçois cet email, la config SMTP fonctionne correctement.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'Email envoyé avec succès à {settings.ADMIN_EMAIL}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur SMTP : {e}'))
