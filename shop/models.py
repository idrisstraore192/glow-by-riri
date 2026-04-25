from django.db import models
from django.utils.text import slugify


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('produits', 'Nos produits'),
        ('perruques', 'Perruques'),
        ('bundles', 'Bundles & Laces'),
    ]
    TYPE_CHOICES = [
        ('produit', 'Produit'),
        ('perruque', 'Perruque'),
        ('lace', 'Lace / Frontale'),
        ('bundle', 'Bundle'),
    ]
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, null=True, verbose_name="URL de l'image (Cloudinary)")
    video_url = models.URLField(blank=True, null=True, verbose_name="URL de la vidéo (Cloudinary)")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='produits', verbose_name="Catégorie")
    product_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='produit', verbose_name="Type", help_text="Détermine la catégorie du produit et son ordre d'affichage.")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Rabais (%)", help_text="Ex: 20 pour -20%. Laisser 0 si aucun rabais.")
    disponible = models.BooleanField(default=True, verbose_name="Disponible", help_text="Décocher pour masquer ce produit du site.")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage", help_text="0 = en premier. Plus le chiffre est grand, plus le produit apparaît en bas.")
    stock = models.PositiveIntegerField(null=True, blank=True, verbose_name="Stock", help_text="Laisser vide pour stock illimité.")
    avec_installation = models.BooleanField(default=False, verbose_name="Option pose (-5%)", help_text="Afficher l'option 'Pose chez Glow by Riri' sur la fiche produit.")
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

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
        ('lace', 'Taille de lace'),
        ('type_lace', 'Type de lace'),
        ('densite', 'Densité'),
        ('couleur', 'Couleur'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="Produit")
    variant_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='longueur', verbose_name="Type")
    label = models.CharField(max_length=50, default='', verbose_name="Option", help_text="Ex: 12 pouces, 13x4 HD, 180%")
    price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Prix")
    photo_url = models.URLField(blank=True, default='', verbose_name="Photo (optionnel)", help_text="Photo qui s'affiche automatiquement quand cette option est sélectionnée")
    stock = models.PositiveIntegerField(null=True, blank=True, verbose_name="Stock", help_text="Laisser vide = illimité. 0 = rupture de stock.")

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
    shipped = models.BooleanField(default=False, verbose_name="Expédiée")
    tracking_number = models.CharField(max_length=200, blank=True, verbose_name="Numéro de suivi")
    shipping_address = models.TextField(blank=True, verbose_name="Adresse de livraison")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commande #{self.id} — {self.customer_name}"


class TutorialSection(models.Model):
    class Meta:
        verbose_name = "📹 Gérer les vidéos tutoriels"
        verbose_name_plural = "📹 Gérer les vidéos tutoriels"

    def __str__(self):
        return "Vidéos tutoriels"


class TutorialVideo(models.Model):
    section = models.ForeignKey(TutorialSection, on_delete=models.CASCADE, related_name='videos', null=True)
    title = models.CharField(max_length=200, verbose_name="Titre")
    video_url = models.URLField(verbose_name="URL de la vidéo (Cloudinary)")
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit lié")
    badge = models.CharField(max_length=50, blank=True, verbose_name="Badge", help_text="Ex: NEW, POPULAIRE")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")

    class Meta:
        verbose_name = "Vidéo tutoriel"
        verbose_name_plural = "Vidéos tutoriels"
        ordering = ['order']

    def __str__(self):
        return self.title


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"


class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Code")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Réduction (%)")
    max_uses = models.IntegerField(null=True, blank=True, verbose_name="Utilisations max")
    uses_count = models.IntegerField(default=0, verbose_name="Utilisations")
    active = models.BooleanField(default=True, verbose_name="Actif")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Expiration")

    class Meta:
        verbose_name = "Code promo"
        verbose_name_plural = "Codes promo"

    def __str__(self):
        return f"{self.code} (-{self.discount_percent}%)"

    def is_valid(self):
        from django.utils import timezone
        if not self.active:
            return False, "Ce code promo n'est pas actif."
        if self.expires_at and self.expires_at < timezone.now():
            return False, "Ce code promo a expiré."
        if self.max_uses is not None and self.uses_count >= self.max_uses:
            return False, "Ce code promo a atteint son nombre d'utilisations maximum."
        return True, "Code valide."


class LaceVariant(models.Model):
    TYPE_CHOICES = [
        ('transparente', 'Transparente'),
        ('hd', 'HD'),
    ]
    TAILLE_CHOICES = [
        ('13x4', '13x4'),
        ('13x6', '13x6'),
        ('4x4', '4x4'),
        ('5x5', '5x5'),
        ('360', '360°'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='lace_variants', verbose_name='Produit')
    type_lace = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='Type')
    taille_lace = models.CharField(max_length=10, choices=TAILLE_CHOICES, verbose_name='Taille')
    longueur = models.CharField(max_length=20, verbose_name='Longueur', help_text='Ex: 10 pouces')
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Prix')
    photo_url = models.URLField(blank=True, default='', verbose_name='Photo (Cloudinary)')
    video_url = models.URLField(blank=True, default='', verbose_name='Vidéo (Cloudinary)')
    stock = models.PositiveIntegerField(null=True, blank=True, verbose_name='Stock', help_text='Laisser vide = illimité. 0 = rupture de stock.')

    class Meta:
        verbose_name = 'Variante lace'
        verbose_name_plural = 'Variantes lace'
        ordering = ['type_lace', 'taille_lace', 'longueur']
        unique_together = ('product', 'type_lace', 'taille_lace', 'longueur')

    def __str__(self):
        return f"{self.get_type_lace_display()} {self.taille_lace} {self.longueur} — {self.price}$"


class WishlistItem(models.Model):
    session_key = models.CharField(max_length=40)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Favori"
        verbose_name_plural = "Favoris"
        unique_together = ('session_key', 'product')


class StockNotification(models.Model):
    email = models.EmailField(verbose_name="Email")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False, verbose_name="Notifiée")

    class Meta:
        verbose_name = "Alerte stock"
        verbose_name_plural = "Alertes stock"
        unique_together = ('email', 'product')

    def __str__(self):
        return f"{self.email} — {self.product.name}"
