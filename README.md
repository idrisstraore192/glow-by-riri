# Glow by Riri

Boutique e-commerce et système de réservation pour **Riri**, coiffeuse à Montréal (Québec, Canada).

**Site en production :** [glowbyriri.store](https://glowbyriri.store)

---

## Stack technique

- **Django 4.2** — framework backend
- **PostgreSQL** — base de données (hébergée sur Railway)
- **Stripe** — paiements en ligne et acomptes de réservation
- **Brevo** — envoi des emails transactionnels
- **Cloudinary** — stockage des images et vidéos
- **Whitenoise** — fichiers statiques
- **Railway** — hébergement et déploiement continu

---

## Fonctionnalités

### Boutique
- Catalogue produits avec variantes (longueurs, types de lace, densité)
- Panier persistant par session
- Paiement Stripe avec webhook anti-doublon
- Codes promo avec dates d'expiration
- Liste de souhaits
- Alertes stock épuisé par email
- Tutoriels vidéo Cloudinary

### Réservations
- Calendrier avec créneaux disponibles
- Paiement d'acompte via Stripe
- Formulaire de demande sans créneau (dépôt/récupération de perruques)
- Notifications email automatiques (cliente + Riri)

### Avis clients
- Dépôt d'avis avec note 1–5
- Modération par Riri depuis l'admin Django

---

## Lancer le projet localement

```bash
# Cloner le repo
git clone https://github.com/idrisstraore192/glow-by-riri.git
cd glow-by-riri

# Créer et activer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env  # puis remplir les valeurs

# Appliquer les migrations
make migrate

# Lancer le serveur
make run
```

Le serveur démarre sur [http://localhost:8000](http://localhost:8000).

---

## Commandes utiles

```bash
make run        # Démarre le serveur local
make test       # Lance les tests automatisés (99 tests, SQLite en mémoire)
make migrate    # Applique les migrations
make migrations # Génère les migrations
make shell      # Shell Django interactif
```

---

## Variables d'environnement requises

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Clé secrète Django |
| `DEBUG` | `True` en local, `False` en prod |
| `DATABASE_URL` | URL PostgreSQL |
| `STRIPE_PUBLIC_KEY` | Clé publique Stripe |
| `STRIPE_SECRET_KEY` | Clé secrète Stripe |
| `STRIPE_WEBHOOK_SECRET` | Secret webhook Stripe |
| `BREVO_API_KEY` | Clé API Brevo (emails) |
| `ADMIN_EMAIL` | Email de notification (Riri) |
| `CLD_CLOUD_NAME` | Cloudinary cloud name |
| `CLD_API_KEY` | Cloudinary API key |
| `CLD_API_TOKEN` | Cloudinary API token |

---

## Structure du projet

```
glow-by-riri/
├── shop/          # Boutique e-commerce (produits, panier, commandes)
├── booking/       # Réservations et créneaux
├── reviews/       # Avis clients
├── core/          # Page d'accueil et pages statiques
├── templates/     # Templates HTML
├── static/        # CSS, JS, images statiques
└── glow_by_riri/  # Configuration Django
```

---

## Déploiement

Le projet est hébergé sur [Railway](https://railway.app). Chaque push sur `main` déclenche un redéploiement automatique. Les migrations sont appliquées au démarrage via le `Procfile`.

**DNS :** Domaine `glowbyriri.store` géré sur Namecheap, pointant vers Railway.
