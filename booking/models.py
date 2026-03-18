from django.db import models

class Service(models.Model):
    CATEGORY_CHOICES = [
        ('coiffure', 'Coiffure'),
        ('perruques', 'Perruques & Lace'),
        ('autres', 'Autres'),
    ]
    name = models.CharField(max_length=200, verbose_name="Nom")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='autres', verbose_name="Catégorie")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Prix")
    duration = models.CharField(max_length=100, blank=True, verbose_name="Durée", help_text="Ex: 1h30")
    description = models.TextField(blank=True, verbose_name="Description")
    image_url = models.URLField(blank=True, null=True, verbose_name="URL de l'image (Cloudinary)")

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return self.name

class Appointment(models.Model):
    customer_name = models.CharField(max_length=200, verbose_name="Nom")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Service")
    date = models.DateField(verbose_name="Date")
    time = models.TimeField(verbose_name="Heure")

    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"

    def __str__(self):
        return f"{self.customer_name} — {self.service.name} le {self.date}"
