
from django.db import models


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('produits', 'Nos produits'),
        ('perruques', 'Perruques & Lace'),
    ]
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, null=True, verbose_name="URL de l'image (Cloudinary)")
    video_url = models.URLField(blank=True, null=True, verbose_name="URL de la vidéo (Cloudinary)")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='produits', verbose_name="Catégorie")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Rabais (%)", help_text="Ex: 20 pour -20%. Laisser 0 si aucun rabais.")

    @property
    def final_price(self):
        if self.discount_percent and self.discount_percent > 0:
            return round(float(self.price) * (1 - float(self.discount_percent) / 100), 2)
        return float(self.price)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Produit")
    image_url = models.URLField(verbose_name="URL de l'image (Cloudinary)")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")

    class Meta:
        verbose_name = "Photo"
        verbose_name_plural = "Photos"
        ordering = ['order']

    def __str__(self):
        return f"Photo de {self.product.name}"


class ProductVariant(models.Model):
    TYPE_CHOICES = [
        ('longueur', 'Longueur'),
        ('fermeture', 'Type de lace'),
        ('densite', 'Densité'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="Produit")
    variant_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='longueur', verbose_name="Type")
    label = models.CharField(max_length=50, default='', verbose_name="Option", help_text="Ex: 12 pouces, 13x4 HD, 180%")
    price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Prix (longueur seulement)")

    class Meta:
        verbose_name = "Variante"
        verbose_name_plural = "Variantes"
        ordering = ['variant_type', 'price', 'label']

    def __str__(self):
        return f"{self.product.name} — {self.get_variant_type_display()} : {self.label}"


class ProductVideo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='videos', verbose_name="Produit")
    video_url = models.URLField(verbose_name="URL de la vidéo (Cloudinary)")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")

    class Meta:
        verbose_name = "Vidéo"
        verbose_name_plural = "Vidéos"
        ordering = ['order']

    def __str__(self):
        return f"Vidéo de {self.product.name}"


class Order(models.Model):
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_session_id = models.CharField(max_length=200, blank=True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commande #{self.id} — {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"
