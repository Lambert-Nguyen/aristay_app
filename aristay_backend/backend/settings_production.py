"""
Production Settings for Aristay
Use this for production deployment
"""

from .settings_base import *
import os

# Using Django's default User model
# AUTH_USER_MODEL = 'auth.User'  # This is the default

# Production overrides
DEBUG = False
DJANGO_ENVIRONMENT = "production"

# Security settings for production
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set in production")

# Allowed hosts from environment
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    raise ValueError("ALLOWED_HOSTS environment variable must be set in production")

# Database from environment (Heroku DATABASE_URL)
DATABASES = {
    'default': dj_database_url.parse(
        os.getenv('DATABASE_URL'),
        conn_max_age=60,
        conn_health_checks=True,
    )
}

# CORS settings for production
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True

# CSRF settings
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')

# Security settings
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'true').lower() == 'true'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Cache configuration (Redis for production)
import ssl

REDIS_URL = os.getenv('REDIS_URL')
if REDIS_URL:
    # Configure Redis with SSL certificate handling
    _redis_use_ssl = os.getenv('REDIS_USE_SSL', '').lower() == 'true' or REDIS_URL.startswith('rediss://')
    _redis_ssl_cert_reqs = os.getenv('REDIS_SSL_CERT_REQS', 'required')
    _redis_ssl_ca_certs = os.getenv('REDIS_SSL_CA_CERTS')
    _redis_ignore_exceptions = os.getenv('REDIS_IGNORE_EXCEPTIONS', 'true').lower() == 'true'

    _redis_options = {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        'CONNECTION_POOL_KWARGS': {
            'max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS', '50')),
            'retry_on_timeout': True,
        },
        'IGNORE_EXCEPTIONS': _redis_ignore_exceptions,
    }

    if _redis_use_ssl:
        # SSL settings for django-redis
        ssl_cert_reqs_value = getattr(ssl, f'CERT_{_redis_ssl_cert_reqs.upper()}', ssl.CERT_REQUIRED)
        _redis_options['CONNECTION_POOL_KWARGS']['ssl_cert_reqs'] = ssl_cert_reqs_value
        if _redis_ssl_ca_certs:
            _redis_options['CONNECTION_POOL_KWARGS']['ssl_ca_certs'] = _redis_ssl_ca_certs
        # Enable SSL for the connection
        _redis_options['CONNECTION_POOL_KWARGS']['ssl'] = True
        
        # Debug logging
        print(f"🔧 Redis SSL Config: USE_SSL={_redis_use_ssl}, CERT_REQS={_redis_ssl_cert_reqs} -> {ssl_cert_reqs_value}, IGNORE_EXCEPTIONS={_redis_ignore_exceptions}")

    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': _redis_options,
            'TIMEOUT': int(os.getenv('CACHE_TIMEOUT', '300')),
        }
    }

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@aristay.com')

# Logging configuration for production
LOGGING['handlers']['file']['filename'] = '/app/logs/debug.log'
LOGGING['handlers']['error_file']['filename'] = '/app/logs/error.log'

# Static files for production
STATIC_ROOT = '/app/staticfiles'

# Media files for production (if using cloud storage)
if os.getenv('USE_CLOUD_STORAGE', 'false').lower() == 'true':
    # Configure cloud storage (AWS S3, etc.)
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_DEFAULT_ACL = None
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Sentry configuration for production
SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_logging = LoggingIntegration(
        level=logging.INFO,        # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_denylist=['django.db.models.signals.pre_save', 'django.db.models.signals.post_save'],
            ),
            sentry_logging,
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment=DJANGO_ENVIRONMENT,
    )

# Performance optimizations
CONN_MAX_AGE = 60

# Disable debug toolbar and other development tools
if 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS.remove('debug_toolbar')
if 'debug_toolbar.middleware.DebugToolbarMiddleware' in MIDDLEWARE:
    MIDDLEWARE.remove('debug_toolbar.middleware.DebugToolbarMiddleware')
