from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from shop.models import Product, ProductVariant, LaceVariant


class Command(BaseCommand):
    help = "Envoie le bilan mensuel du stock à l'administrateur"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        month = now.strftime("%B %Y")
        lines = [f"Bilan du stock — {month}\n", "=" * 40]

        products = Product.objects.filter(disponible=True).prefetch_related(
            'variants', 'lace_variants'
        ).order_by('product_type', 'order', 'name')

        for product in products:
            stock_str = str(product.stock) if product.stock is not None else "illimité"
            alert = " ⚠️ RUPTURE" if product.stock == 0 else ""
            lines.append(f"\n{product.name} (stock général : {stock_str}){alert}")

            variants = list(product.variants.all())
            if variants:
                for v in variants:
                    v_stock = str(v.stock) if v.stock is not None else "illimité"
                    v_alert = " ⚠️ RUPTURE" if v.stock == 0 else ""
                    lines.append(f"  • {v.get_variant_type_display()} {v.label} — {v_stock}{v_alert}")

            lace_variants = list(product.lace_variants.all())
            if lace_variants:
                for lv in lace_variants:
                    lv_stock = str(lv.stock) if lv.stock is not None else "illimité"
                    lv_alert = " ⚠️ RUPTURE" if lv.stock == 0 else ""
                    lines.append(
                        f"  • {lv.get_type_lace_display()} {lv.taille_lace} {lv.longueur} — {lv_stock}{lv_alert}"
                    )

        lines.append("\n\nGlow by Riri")
        message = "\n".join(lines)

        send_mail(
            subject=f"📦 Bilan mensuel du stock — {month}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Bilan envoyé pour {month}"))
