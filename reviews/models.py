from django.db import models

class Review(models.Model):
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    name = models.CharField(max_length=100, verbose_name="Nom")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, verbose_name="Note")
    comment = models.TextField(verbose_name="Commentaire")
    approved = models.BooleanField(default=False, verbose_name="Approuvé")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Avis"
        verbose_name_plural = "Avis"

    def __str__(self):
        return f"{self.name} — {self.rating}★"
