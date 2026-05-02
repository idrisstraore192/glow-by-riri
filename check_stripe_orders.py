"""
Script d'audit : liste toutes les sessions Stripe 'completed' des 30 derniers jours.
Usage: railway run python check_stripe_orders.py
"""
import os
import stripe
from datetime import datetime, timezone, timedelta

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

cutoff = datetime.now(timezone.utc) - timedelta(days=90)
cutoff_ts = int(cutoff.timestamp())

print("=== Audit Stripe — sessions checkout.session.completed ===\n")

sessions = stripe.checkout.Session.list(limit=100, created={"gte": cutoff_ts})
count = 0
for s in sessions.auto_paging_iter():
    if s.payment_status != "paid":
        continue
    meta = s.get("metadata") or {}
    if meta.get("type") != "order":
        continue
    count += 1
    created = datetime.fromtimestamp(s.created, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
    name  = s.customer_details.name  if s.customer_details else "?"
    email = s.customer_details.email if s.customer_details else "?"
    total = s.amount_total / 100
    print(f"  {created}  |  {name} <{email}>  |  {total:.2f} CAD  |  {s.id}")

print(f"\n{count} commande(s) payée(s) sur Stripe (90 derniers jours).")
