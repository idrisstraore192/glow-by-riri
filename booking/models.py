from django.db import models

class Service(models.Model):
    CATEGORY_CHOICES = [
        ('coiffure', 'Coiffure'),
    ]
    name = models.CharField(max_length=200, verbose_name="Nom")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='autres', verbose_name="Catégorie")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Prix")
    duration = models.CharField(max_length=100, blank=True, verbose_name="Durée", help_text="Ex: 1h30")
    description = models.TextField(blank=True, verbose_name="Description")
    image_url = models.URLField(blank=True, null=True, verbose_name="URL de l'image (Cloudinary)")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Rabais (%)", help_text="Ex: 20 pour -20%. Laisser 0 si aucun rabais.")

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['price']

    @property
    def final_price(self):
        if self.discount_percent and self.discount_percent > 0:
            return round(float(self.price) * (1 - float(self.discount_percent) / 100), 2)
        return float(self.price)

    def __str__(self):
        return self.name

class ServiceImage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='images', verbose_name="Service")
    image_url = models.URLField(verbose_name="URL de l'image (Cloudinary)")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")

    class Meta:
        verbose_name = "Photo du service"
        verbose_name_plural = "Photos du service"
        ordering = ['order']

    def __str__(self):
        return f"Photo de {self.service.name}"


class AvailabilitySlot(models.Model):
    date = models.DateField(verbose_name="Date")
    time = models.TimeField(verbose_name="Heure")
    is_booked = models.BooleanField(default=False, verbose_name="Réservé")

    class Meta:
        ordering = ['date', 'time']
        verbose_name = "Créneau disponible"
        verbose_name_plural = "Créneaux disponibles"
        unique_together = ['date', 'time']

    def __str__(self):
        days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        months = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
        day_name = days[self.date.weekday()]
        month_name = months[self.date.month - 1]
        return f"{day_name} {self.date.day} {month_name} {self.date.year} à {self.time.strftime('%H h %M')}"


class Appointment(models.Model):
    customer_name = models.CharField(max_length=200, verbose_name="Nom")
    customer_email = models.EmailField(blank=True, verbose_name="Email")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Service")
    slot = models.ForeignKey(AvailabilitySlot, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Créneau")
    date = models.DateField(verbose_name="Date")
    time = models.TimeField(verbose_name="Heure")
    deposit_paid = models.BooleanField(default=False, verbose_name="Acompte payé (20 $)")
    stripe_session_id = models.CharField(max_length=200, blank=True, verbose_name="Session Stripe")
    reminder_sent = models.BooleanField(default=False, verbose_name="Rappel envoyé")

    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"

    def __str__(self):
        return f"{self.customer_name} — {self.service.name} le {self.date}"
