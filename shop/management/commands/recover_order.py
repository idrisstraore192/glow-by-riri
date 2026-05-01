"""
Management command: recover_order
Usage: python manage.py recover_order <stripe_session_id>

Fetches the Stripe checkout session, creates the Order + OrderItems in the DB,
and sends notification emails to the admin and the customer.
Idempotent: skips creation if the order already exists for this session.
"""
import stripe
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from shop.models import Order, OrderItem
from shop.views import _send_order_emails

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Recover a missing order from a Stripe checkout session ID"

    def add_arguments(self, parser):
        parser.add_argument("session_id", type=str, help="Stripe checkout session ID (cs_live_...)")
        parser.add_argument("--dry-run", action="store_true", help="Print details without saving")

    def handle(self, *args, **options):
        session_id = options["session_id"]
        dry_run = options["dry_run"]

        stripe.api_key = settings.STRIPE_SECRET_KEY
        if not stripe.api_key:
            raise CommandError("STRIPE_SECRET_KEY is not set.")

        # Check idempotency
        if Order.objects.filter(stripe_session_id=session_id).exists():
            self.stdout.write(self.style.WARNING(
                f"Order already exists for session {session_id} — nothing to do."
            ))
            return

        self.stdout.write(f"Fetching Stripe session {session_id} ...")
        try:
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=["shipping_cost.shipping_rate"],
            )
        except stripe.error.StripeError as e:
            raise CommandError(f"Stripe error: {e}")

        if session.payment_status != "paid":
            raise CommandError(f"Session payment_status is '{session.payment_status}' — not paid. Aborting.")

        # Shipping address
        shipping_name = ""
        if session.shipping_cost and session.shipping_cost.shipping_rate:
            shipping_name = session.shipping_cost.shipping_rate.display_name or ""
        is_pickup = "main propre" in shipping_name.lower()
        if is_pickup:
            shipping_address = "Remise en main propre"
        else:
            addr = session.shipping_details.address if session.shipping_details else None
            shipping_address = ""
            if addr:
                parts = [addr.line1, addr.line2, addr.city, addr.state, addr.postal_code, addr.country]
                shipping_address = ", ".join(p for p in parts if p)

        customer_name = (session.customer_details.name if session.customer_details else None) or "Cliente"
        customer_email = (session.customer_details.email if session.customer_details else None) or ""
        total = session.amount_total / 100

        self.stdout.write(f"  Customer : {customer_name} <{customer_email}>")
        self.stdout.write(f"  Total    : {total:.2f} CAD")
        self.stdout.write(f"  Address  : {shipping_address}")

        # Line items
        line_items_response = stripe.checkout.Session.list_line_items(session_id)
        self.stdout.write("  Items:")
        for li in line_items_response.data:
            unit_price = li.amount_total / 100 / (li.quantity or 1)
            self.stdout.write(f"    - {li.description}  x{li.quantity}  @ {unit_price:.2f} $")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — not saving."))
            return

        # Create order
        order = Order.objects.create(
            customer_name=customer_name,
            customer_email=customer_email,
            total=total,
            stripe_session_id=session_id,
            shipping_address=shipping_address,
            paid=True,
        )
        self.stdout.write(f"  Created Order #{order.id}")

        items_for_email = []
        for li in line_items_response.data:
            unit_price = li.amount_total / 100 / (li.quantity or 1)
            oi = OrderItem.objects.create(
                order=order,
                product=None,
                product_name=li.description or "Article",
                price=unit_price,
                quantity=li.quantity or 1,
            )
            items_for_email.append({
                "product": None,
                "product_name": oi.product_name,
                "label": None,
                "quantity": oi.quantity,
                "price": str(oi.price),
            })

        self.stdout.write("  Sending emails ...")
        _send_order_emails(order, items_for_email)
        self.stdout.write(self.style.SUCCESS(
            f"Order #{order.id} created and emails sent for session {session_id}."
        ))
