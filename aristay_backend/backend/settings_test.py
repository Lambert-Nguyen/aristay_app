"""
Test Settings for Aristay
Use this for running tests
"""

import os

from .settings_base import *

# Using Django's default User model
# AUTH_USER_MODEL = 'auth.User'  # This is the default

# Test-specific overrides
DEBUG = True
DJANGO_ENVIRONMENT = "testing"
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

# Prefer DATABASE_URL in CI/local if provided, else fall back to local Postgres
from pathlib import Path
import dj_database_url

_db_url = os.getenv('DATABASE_URL')
if _db_url:
    DATABASES = {
        'default': dj_database_url.parse(_db_url, conn_max_age=0, ssl_require=False),
    }
else:
    # Local Postgres default for tests
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'aristay_test'),
            'USER': os.getenv('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'postgres'),
            'HOST': os.getenv('POSTGRES_HOST', '127.0.0.1'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': 0,
        }
    }

# Run real migrations in tests to match CI behavior

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

# Remove Axes middleware and apps from MIDDLEWARE and INSTALLED_APPS during tests
MIDDLEWARE = [m for m in MIDDLEWARE if not m.startswith('axes.')]
INSTALLED_APPS = [app for app in INSTALLED_APPS if not app.startswith('axes')]

# Completely disable Axes to prevent any loading
os.environ['AXES_ENABLED'] = 'False'

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

# Override STORAGES to ensure local filesystem is used (not Cloudinary)
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
        'OPTIONS': {
            'location': '/tmp/test_media',
        },
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

# Mock Cloudinary settings to prevent "Must supply api_key" errors during tests
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'test_cloud',
    'API_KEY': 'test_key',
    'API_SECRET': 'test_secret',
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
TIME_ZONE = 'America/New_York'  # Tampa, FL timezone to match production

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

# Add MAX_UPLOAD_BYTES for tests
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25MB default for tests

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

# Ensure Cloudinary is properly mocked
os.environ['CLOUDINARY_CLOUD_NAME'] = 'test_cloud'
os.environ['CLOUDINARY_API_KEY'] = 'test_key'
os.environ['CLOUDINARY_API_SECRET'] = 'test_secret'
