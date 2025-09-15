"""
Test Settings for Aristay
Use this for running tests
"""

import os

# Force-disable DATABASE_URL so base settings don't connect to Postgres during tests
os.environ["DATABASE_URL"] = ""

from .settings_base import *

# Using Django's default User model
# AUTH_USER_MODEL = 'auth.User'  # This is the default

# Test-specific overrides
DEBUG = True
DJANGO_ENVIRONMENT = "testing"

# Use SQLite for tests to avoid GiST constraint issues
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

# Disable API app migrations for tests (avoid Postgres-specific SQL like DO $$ blocks)
# Disable all migrations for tests. Django will create tables directly from models.
# Disable api migrations only; point to empty module to force syncdb
MIGRATION_MODULES = {
    'api': None,
}

# Disable password hashing for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Disable cache during tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable email sending during tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable Axes during tests
AXES_ENABLED = False

# Remove Axes middleware from MIDDLEWARE during tests
MIDDLEWARE = [m for m in MIDDLEWARE if not m.startswith('axes.')]

# Disable security features during tests
SECURE_SSL_REDIRECT = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False

# Test-specific settings
TESTING = True

# Disable Cloudinary entirely during tests and force local file storage
USE_CLOUDINARY = False
os.environ['USE_CLOUDINARY'] = 'false'

# Remove cloudinary apps to prevent backend initialization during tests
INSTALLED_APPS = [
    app for app in INSTALLED_APPS
    if app not in ('cloudinary', 'cloudinary_storage')
]

# Storage backends: use local filesystem for both default and staticfiles
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

# Ensure Django knows we're testing
os.environ['TESTING'] = 'true'

# Some third-party packages still respect legacy settings
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Disable media files during tests
MEDIA_ROOT = '/tmp/test_media'

# Disable session security during tests
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Disable CORS during tests
CORS_ALLOW_ALL_ORIGINS = True

# Enable timezone for tests to support timezone-aware datetimes
USE_TZ = True
TIME_ZONE = 'UTC'

# Ensure throttle rates are available for tests
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/minute',
        'password_reset': '3/hour',
        'token_refresh': '2/minute',
        'admin_api': '500/hour',
        'evidence_upload': '15/minute',
        'taskimage': '15/minute',
    }
}

# Add missing apps for tests (avoid duplicates)
if 'rest_framework.authtoken' not in INSTALLED_APPS:
    INSTALLED_APPS = INSTALLED_APPS + [
        'rest_framework.authtoken',
    ]

# Add authentication backends for tests (exclude Axes)
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'rest_framework_simplejwt.authentication.JWTAuthentication',
]
