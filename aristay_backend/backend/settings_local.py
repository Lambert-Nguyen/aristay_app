"""
Local Development Settings (Heroku-compatible)
Use this for local development with PostgreSQL
"""

from .settings import *

# Override database to use PostgreSQL for local development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "aristay_local",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "127.0.0.1",
        "PORT": "5432",
        "CONN_MAX_AGE": 60,
    }
}

# Local development settings
DEBUG = True
DJANGO_ENVIRONMENT = "development"

# Security settings for local development
SECRET_KEY = "local-dev-secret-key-change-me"
JWT_SIGNING_KEY = "local-jwt-key-change-me"

# CORS and Hosts for local development
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000", 
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

# Email backend for local development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable SSL redirect for local development
SECURE_SSL_REDIRECT = False

# Optional: Use local Redis if available
# REDIS_URL = "redis://127.0.0.1:6379/1"

print("🔧 Using local development settings with PostgreSQL")
