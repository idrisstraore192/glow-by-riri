# Glow by Riri — Guide du projet

## Vue d'ensemble

Boutique e-commerce + système de réservation pour Riri, coiffeuse à Montréal (Québec, Canada).
Stack : **Django 4.2** · **PostgreSQL** (prod Railway) · **Stripe** · **Brevo** (emails) · **Cloudinary** (médias) · **Whitenoise** (static)

Site en production : **https://glowbyriri.store**
Admin Railway : **https://glowbyriri.store/admin/**
Repo GitHub : https://github.com/idrisstraore192/glow-by-riri

---

## Commandes essentielles

```bash
make test       # Lance les 99 tests automatisés (SQLite en mémoire)
make run        # Démarre le serveur local
make migrate    # Applique les migrations
make migrations # Génère les migrations
make shell      # Shell Django interactif
```

---

## Architecture des apps

### `shop/` — Boutique e-commerce
**Modèles :**
- `Product` — produit avec `product_type` (produits / perruques / bundles), `available`, `discount_pct`
- `ProductVariant` — variantes avec stock et prix (ex: longueurs de cheveux)
- `LaceVariant` — variantes pour bundles/laces avec couleur/longueur/stock
- `ProductImage`, `ProductVideo` — médias produit
- `Order` / `OrderItem` — commandes Stripe avec `stripe_session_id` (anti-doublon)
- `PromoCode` — codes promo avec date d'expiration et `max_uses`
- `TutorialSection` / `TutorialVideo` — vidéos tutoriels Cloudinary
- `WishlistItem` — favoris par session
- `StockNotification` — alertes stock épuisé email à Riri

**Flux de paiement :**
1. `checkout` → crée session Stripe → redirige vers Stripe
2. Stripe webhook (`/shop/stripe/webhook/`) → crée `Order` + `OrderItem` → envoie emails
3. `payment_success` → vérifie `stripe_session_id` (anti-doublon) → affiche confirmation

**Anti-doublon commande :** `payment_success` vérifie `Order.objects.filter(stripe_session_id=session_id).first()` avant de créer.

**Panier (session) :** `shop/cart.py` — clés de session : `simple_{product_id}`, `variant_{variant_id}`, `lace_{lace_id}`, `pose_{product_id}`

### `booking/` — Réservations
**Modèles :**
- `Service` — service avec `price`, `deposit_amount`, `nattes_requises`, `sans_creneau` (bool), `order` (int, tri)
- `AvailabilitySlot` — créneaux date/heure avec `is_booked`
- `Appointment` — RDV avec `deposit_paid`, `stripe_session_id`, `nattes_deja_faites`
- `ServiceRequest` — demandes sans créneau (dépôt/récupération), `contacted` bool

**Deux flux de réservation :**
- Services normaux → `/booking/` → calendrier + Stripe (acompte)
- Services `sans_creneau=True` → `/booking/demande/` → formulaire simple, email à Riri, pas de paiement

**Ordre d'affichage services :** champ `order` (int) — valeur élevée = apparaît en dernier dans la liste.

### `reviews/` — Avis clients
- `Review` avec `approved` bool — les avis non approuvés n'apparaissent pas
- Modération dans l'admin

### `core/` — Pages statiques
- Page d'accueil (`/`)

---

## Emails

**Backend :** Brevo (anymail) via variable `BREVO_API_KEY`
**From :** `Glow by Riri <glowbyririi@gmail.com>`
**Admin email :** `ADMIN_EMAIL` (env var, défaut `glowbyririi@gmail.com`)

**Règle critique :** Ne jamais utiliser `fail_silently=True`. Toujours :
```python
try:
    send_mail(..., fail_silently=False)
except Exception as e:
    logger.error(f"Email error: {e}")
```

**Emails envoyés :**
- Nouvelle commande → Riri + cliente (HTML + texte)
- Nouveau RDV confirmé → Riri + cliente
- Nouvelle demande sans créneau → Riri
- Stock épuisé → Riri (quand un variant tombe à 0)
- Rapport mensuel stock → `send_stock_report` management command

---

## Variables d'environnement (Railway)

| Variable | Usage |
|----------|-------|
| `SECRET_KEY` | Clé Django |
| `DEBUG` | `False` en prod |
| `DATABASE_URL` | PostgreSQL Railway |
| `ALLOWED_HOSTS` | `glowbyriri.store,glowbyriri.up.railway.app` |
| `CSRF_TRUSTED_ORIGINS` | `https://glowbyriri.store,https://glowbyriri.up.railway.app` |
| `STRIPE_PUBLIC_KEY` | Clé publique Stripe |
| `STRIPE_SECRET_KEY` | Clé secrète Stripe |
| `STRIPE_WEBHOOK_SECRET` | Secret webhook Stripe |
| `BREVO_API_KEY` | API Brevo pour les emails |
| `ADMIN_EMAIL` | Email de Riri pour les notifications |
| `CLD_CLOUD_NAME` | Cloudinary cloud name |
| `CLD_API_KEY` | Cloudinary API key |
| `CLD_API_TOKEN` | Cloudinary API token |

---

## Tests

```bash
make test
# ou
python3 manage.py test shop booking --settings=glow_by_riri.settings_test
```

**Configuration test (`settings_test.py`) :**
- SQLite en mémoire (pas PostgreSQL)
- `MIGRATION_MODULES = {app: None}` pour contourner les migrations PostgreSQL-spécifiques (migration 0024 utilise du SQL brut)
- Email backend `locmem`
- Password hasher MD5 (plus rapide)

**Nommage des fichiers de tests :**
- `shop/tests_shop.py` (pas `tests.py` — collision de modules)
- `booking/tests_booking.py`

**Ne pas nommer les management commands `test_*.py`** — Django les découvre comme des tests. Le bon nom : `send_test_email.py`.

---

## Déploiement

- Push sur `main` → Railway redéploie automatiquement
- Migrations appliquées automatiquement au démarrage (`migrate` dans Procfile ou Railway)
- Static files servis par Whitenoise

**DNS :**
- Domaine : Namecheap (`glowbyriri.store`)
- CNAME `@` → `jsthehpb.up.railway.app`
- TXT `_railway` → `railway-verify=32dad3f...`

---

## Pièges connus

1. **Duplicate `{% block title %}` dans base.html** → TemplateSyntaxError 500
2. **`django.contrib.sitemaps` nécessite `django.contrib.sites`** + `SITE_ID = 1`
3. **`fail_silently=True` + `except Exception`** → l'exception est avalée avant d'atteindre le `except`
4. **`payment_success` sans vérification `stripe_session_id`** → commandes en double si webhook + redirect arrivent simultanément
5. **Migration 0024** utilise du SQL PostgreSQL brut → incompatible SQLite → utiliser `settings_test.py` pour les tests
6. **Management command `test_email.py`** → renommée `send_test_email.py` (pattern `test*.py` détecté comme test)

---

## Structure des templates

```
templates/
├── base.html              # Layout global, nav, footer, SEO meta tags
├── 404.html               # Page d'erreur personnalisée
├── booking/
│   ├── booking.html       # Page réservation + services + avis
│   ├── service_request.html      # Formulaire demande sans créneau
│   ├── service_request_success.html
│   ├── success.html       # Confirmation RDV
│   └── deposit_cancel.html
├── shop/
│   ├── products.html      # Liste produits + tutoriels vidéo
│   ├── product_detail.html
│   ├── cart.html
│   ├── checkout.html
│   └── payment_success.html
├── emails/
│   └── appointment_confirmation.html
└── core/
    └── home.html
```

---

## Fonctionnalités à compléter (non fait)

- [ ] Pages légales (politique de confidentialité, retours, CGV)
- [ ] Page "À propos"
- [ ] Google Analytics (en attente de l'ID GA4 de Riri)
- [ ] Google Business Profile
- [ ] Bannière cookies
- [ ] Bouton WhatsApp flottant
