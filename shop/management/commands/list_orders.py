from django.core.management.base import BaseCommand
from shop.models import Order


class Command(BaseCommand):
    help = "List all orders in the database"

    def handle(self, *args, **options):
        orders = Order.objects.prefetch_related('items').order_by('-created_at')
        self.stdout.write(f"Total orders: {orders.count()}\n")
        for o in orders:
            items = ', '.join(f"{oi.quantity}x {oi.product_name}" for oi in o.items.all())
            self.stdout.write(
                f"  #{o.id} | {o.created_at.strftime('%Y-%m-%d %H:%M')} | "
                f"{o.customer_name} <{o.customer_email}> | "
                f"{float(o.total):.2f} CAD | paid={o.paid}"
            )
            self.stdout.write(f"       {items}")
            self.stdout.write(f"       Livraison: {o.shipping_address[:60]}")
