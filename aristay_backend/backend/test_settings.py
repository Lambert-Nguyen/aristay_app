"""
Test - specific Django settings for AriStay Backend
Optimized for fast, reliable automated testing
"""

import os
import sys

from .settings import *

# Override settings for testing

# Database - Use in - memory SQLite for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {
            "timeout": 5,
        },
    }
}

# If PostgreSQL is available (like in GitHub Actions), use it
if os.environ.get("DATABASE_URL"):
    try:
        import dj_database_url

        DATABASES["default"] = dj_database_url.parse(os.environ.get("DATABASE_URL"))
    except ImportError:
        # Fallback to manual parsing if dj_database_url is not available
        database_url = os.environ.get("DATABASE_URL")
        if database_url.startswith("postgres://"):
            DATABASES["default"] = {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "aristay_test",
                "USER": "postgres",
                "PASSWORD": "postgres",
                "HOST": "localhost",
                "PORT": "5432",
            }


# Disable migrations for faster testing
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


# Comment out the line below if you need to test migrations
MIGRATION_MODULES = DisableMigrations()

# Speed up password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests to reduce noise
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
}

# Disable caching for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Test - specific settings
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Use local storage for media files during testing
MEDIA_ROOT = os.path.join(BASE_DIR, "test_media")

# Disable email sending during tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Test - specific security settings
SECRET_KEY = "test - secret - key - not - for - production"
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

# Disable CSRF for API testing
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Test database settings
if "test" in sys.argv:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {
            "timeout": 5,
        },
    }

# Celery settings for testing (if you use Celery)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Static files for testing
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Test - specific apps (if any)
# Using Django's default test runner instead of nose
# INSTALLED_APPS = INSTALLED_APPS + [
#     "django_nose",  # Add if using nose for testing
# ]

# Use Django's default test runner
# TEST_RUNNER = "django_nose.NoseTestSuiteRunner"
# NOSE_ARGS = [
#     "--with - coverage",
#     "--cover - package=api",
#     "--cover - html",
#     "--cover - html - dir=coverage_html",
#     "--verbosity=2",
# ]

# Time zone for consistent testing
USE_TZ = True
TIME_ZONE = "UTC"

# Internationalization for testing
LANGUAGE_CODE = "en - us"
USE_I18N = True

# File upload settings for testing
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Security settings for testing
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False

# Test - specific middleware (remove security middleware that might interfere)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# CORS settings for testing
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# REST Framework settings for testing
REST_FRAMEWORK.update(
    {
        "TEST_REQUEST_DEFAULT_FORMAT": "json",
        "TEST_REQUEST_RENDERER_CLASSES": [
            "rest_framework.renderers.JSONRenderer",
        ],
    }
)

# Disable throttling for tests
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}

print("📋 Test settings loaded - optimized for automated testing")
