
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
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='produits', verbose_name="Catégorie")

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
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="Produit")
    size = models.CharField(max_length=50, verbose_name="Taille", help_text="Ex: 12 pouces")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Prix")

    class Meta:
        verbose_name = "Variante"
        verbose_name_plural = "Variantes"
        ordering = ['price']

    def __str__(self):
        return f"{self.product.name} — {self.size}"


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
