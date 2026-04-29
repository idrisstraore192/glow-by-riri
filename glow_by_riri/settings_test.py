"""
Settings for automated tests.
Bypasses raw-SQL PostgreSQL migrations by creating tables directly from models.
"""
from .settings import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Skip migrations — Django creates tables from models directly (syncdb-style).
# This avoids PostgreSQL-specific raw SQL in shop/migrations/0024.
MIGRATION_MODULES = {
    "shop": None,
    "booking": None,
    "core": None,
    "reviews": None,
    "auth": None,
    "contenttypes": None,
    "sessions": None,
    "admin": None,
}

# Disable password hashing for faster tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Silence email backend during tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
