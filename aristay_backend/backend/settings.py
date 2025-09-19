"""
Django settings for backend project.
Environment-aware settings that automatically loads the appropriate configuration.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
from pathlib import Path
import ssl

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Load .env file FIRST before environment detection ---
# Skip loading .env during tests/CI so test overrides win
_is_testing = bool(os.getenv('PYTEST_CURRENT_TEST') or os.getenv('TESTING') or os.getenv('CI'))
if not _is_testing and os.getenv("LOAD_DOTENV", "true").lower() == "true":
    try:
        from dotenv import load_dotenv
        for _candidate in [(BASE_DIR / ".env"), (BASE_DIR.parent / ".env")]:
            try:
                if _candidate.exists():
                    load_dotenv(_candidate, override=True)
                    break
            except Exception:
                pass
    except Exception:
        pass
# ---------------------------------------------------

# Determine environment AFTER loading .env
# Force testing environment when running under pytest/CI regardless of .env
if _is_testing:
    os.environ['DJANGO_ENVIRONMENT'] = 'testing'
    os.environ.setdefault('USE_CLOUDINARY', 'false')

# Also check for CI environment variable (common in CI systems)
if os.getenv('CI') or os.getenv('GITHUB_ACTIONS') or os.getenv('GITLAB_CI'):
    os.environ['DJANGO_ENVIRONMENT'] = 'testing'
    os.environ.setdefault('USE_CLOUDINARY', 'false')
    os.environ.setdefault('TESTING', 'true')

DJANGO_ENVIRONMENT = os.getenv('DJANGO_ENVIRONMENT', 'development')

# Load appropriate settings based on environment
if DJANGO_ENVIRONMENT == 'production':
    from .settings_production import *
elif DJANGO_ENVIRONMENT == 'testing':
    from .settings_test import *
else:  # development
    from .settings_local import *


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-*g+qjl3q3q8h1tnkws9(sd^tm(t!ld8rtdre6r5yc+d=jw_yn!')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'

def get_local_ip():
    s = None
    try:
        # This creates a temporary connection to determine your IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        if s:
            s.close()
    return ip

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',') + [get_local_ip()]

# Application definition

# Cloudinary Integration (toggleable via environment variable)
USE_CLOUDINARY = os.getenv('USE_CLOUDINARY', 'false').lower() == 'true'

# Common base apps that should always be present
COMMON_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'api.apps.ApiConfig',  # GPT agent fix: use app config for signal registration
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",  # needed for revoke/blacklist
    "corsheaders",
    "django_filters",
    "axes",
    "drf_spectacular",  # OpenAPI 3 documentation
    "django_crontab",   # Cron job management
    "django_extensions",  # Development tools (show_urls, etc.)
]

if USE_CLOUDINARY:
    # Add Cloudinary to installed apps
    INSTALLED_APPS = COMMON_APPS + [
        'cloudinary',
        'cloudinary_storage',
    ]
    
    # Cloudinary configuration using CLOUDINARY_URL (recommended approach)
    # The CLOUDINARY_URL format automatically configures all settings
    # No additional CLOUDINARY_STORAGE config needed when using CLOUDINARY_URL
    
    # Django 5.x STORAGES configuration for Cloudinary
    STORAGES = {
        "default": {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
else:
    # Standard installed apps (existing configuration)
    INSTALLED_APPS = COMMON_APPS
    
    # Django 5.x STORAGES configuration for local filesystem
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }

# Force local storage and simple staticfiles during tests/CI regardless of env
if os.getenv('TESTING') or os.getenv('CI') or DJANGO_ENVIRONMENT == 'testing':
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # Add CORS middleware near top
    "axes.middleware.AxesMiddleware",  # before AuthenticationMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    # Django's auth middleware must run before you try to use request.user
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Admin access control middleware (must run after authentication)
    "backend.middleware.AdminAccessMiddleware",
    # Agent's Phase 2: Audit middleware for request context capture
    "api.audit_middleware.AuditMiddleware",
    # Now your timezone middleware can safely reference request.user
    "backend.middleware.TimezoneMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "backend.memory_middleware.MemoryManagementMiddleware",  # Memory management
    # Production logging and monitoring middleware
    "backend.middleware.RequestLoggingMiddleware",
    "backend.middleware.ErrorLoggingMiddleware", 
    # Exception middleware runs last (process_exception runs in reverse order)
    "api.middleware.ApiExceptionMiddleware",  # Catch all unhandled exceptions for API endpoints
    "api.enhanced_security_middleware.SecurityHeadersEnhancedMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'api' / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# Add your REST framework configuration here:
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',  # Keep for backward compatibility during transition
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/minute',
        'password_reset': '3/hour',
        'token_refresh': '2/minute',  # More restrictive - refreshes should be infrequent
        'admin_api': '500/hour',
        'evidence_upload': '15/minute',  # Agent's recommendation: Standardized rate for large file uploads
        # Maintain backward compatibility for tests expecting 'taskimage'
        'taskimage': '15/minute',
        'evidence_upload': '15/minute',
        'api': '1000/hour',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# OpenAPI/Swagger Configuration  
SPECTACULAR_SETTINGS = {
    "TITLE": "AriStay API",
    "DESCRIPTION": "Internal APIs for portal, mobile, and admin surfaces.",
    "VERSION": os.getenv("APP_VERSION", "1.0.0"),
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "COMPONENT_SPLIT_REQUEST": True,
    "SECURITY": [{"jwtAuth": []}],
    "AUTHENTICATION_WHITELIST": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "SECURITY_SCHEMES": {
        "jwtAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    },
}

# Swagger UI Settings
SWAGGER_UI_SETTINGS = {
    "persistAuthorization": True,  # Keep Bearer token across reloads
}

# JWT Configuration removed here - see comprehensive config below

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {}
}

# Prefer DATABASE_URL if present (Heroku/Prod/CI)
_db_url = os.getenv("DATABASE_URL")
if _db_url:
    DATABASES["default"] = dj_database_url.parse(_db_url, conn_max_age=60, ssl_require=False)
else:
    # Default to PostgreSQL for local development
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "aristay_local"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": int(os.getenv("POSTGRES_PORT", "5432")),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "sslmode": "prefer",  # Use SSL if available, but don't require it
        },
    }

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Messages framework configuration
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"  # System default: Tampa, FL (Eastern Time)

# AriStay Timezone Configuration
ARISTAY_DEFAULT_TIMEZONE = "America/New_York"  # Tampa, FL
ARISTAY_TIMEZONE_DISPLAY_NAME = "Tampa, FL"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [ BASE_DIR / 'static' ]    # so project-level static/ is on the path
STATIC_ROOT = BASE_DIR / 'staticfiles'        # for collectstatic in production

# === Add these for media uploads ===
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Data upload settings - Agent's enhanced image processing configuration
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000  # Allow up to 10,000 fields for bulk admin operations
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB - Allow large image uploads before our processing

# Image Upload & Processing Configuration
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))  # 25MB ingress limit
STORED_IMAGE_TARGET_BYTES = int(os.getenv("STORED_IMAGE_TARGET_BYTES", str(5 * 1024 * 1024)))  # 5MB storage target
STORED_IMAGE_MAX_DIM = int(os.getenv("STORED_IMAGE_MAX_DIM", "2048"))  # 2048px max dimension

# Audit System Configuration
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
AUDIT_MAX_CHANGES_BYTES = int(os.getenv("AUDIT_MAX_CHANGES_BYTES", "10000"))

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# the URL your users will click through to finish activation/reset
# (point this at your front-end, e.g. localhost:3000)
FRONTEND_URL = "http://localhost:3000"

# ============================================================================
# MEMORY MANAGEMENT CONFIGURATION
# ============================================================================
# Optimize memory usage for Heroku dynos
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB

# Database connection management
DATABASES['default'].update({
    'CONN_MAX_AGE': 60,  # Close connections after 60 seconds
})

# Cache configuration for better memory management
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,  # Limit cache entries
            'CULL_FREQUENCY': 3,  # Remove 1/3 of entries when max reached
        }
    }
}

# ============================================================================
# EMAIL CONFIGURATION (single source of truth)
# ============================================================================
# Use console backend in development to print emails instead of sending
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # In production, use console backend if no SMTP credentials are provided
    # This prevents connection refused errors when SMTP is not configured
    if os.getenv('EMAIL_HOST_USER') and os.getenv('EMAIL_HOST_PASSWORD'):
        EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    else:
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost' if DEBUG else 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '1025' if DEBUG else '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'false' if DEBUG else 'true').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@aristay-internal.cloud')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# CORS configuration
CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'true').lower() == 'true'
CORS_ALLOWED_ORIGINS = [
    origin.strip() 
    for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') 
    if origin.strip()
]

FCM_SERVER_KEY = "your-firebase-server-key-here"
FIREBASE_PROJECT_ID = 'aristayapp'
FIREBASE_CREDENTIALS_FILE = BASE_DIR / 'firebase_credentials.json'

# --- Email digest feature flag ---------------------------------
# Default: OFF.  Turn ON with   export EMAIL_DIGEST_ENABLED=true
EMAIL_DIGEST_ENABLED = os.getenv("EMAIL_DIGEST_ENABLED", "false").lower() == "true"

# Run the digest at this UTC hour (0-23).  Overridable per env.
EMAIL_DIGEST_HOUR_UTC = int(os.getenv("EMAIL_DIGEST_HOUR_UTC", "12"))

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

CRONJOBS = [
    (
        f"0 {EMAIL_DIGEST_HOUR_UTC} * * *",
        "django.core.management.call_command",
        ["send_digest"],
        {"stdout": str(LOG_DIR / "digest.log"),
         "stderr": str(LOG_DIR / "digest_err.log")},
    ),
]

CRONTAB_DJANGO_SETTINGS = "backend.settings"

# ============================================================================
# PRODUCTION LOGGING & MONITORING CONFIGURATION
# ============================================================================

# Environment configuration
ENVIRONMENT = os.getenv('DJANGO_ENVIRONMENT', 'development')
VERSION = os.getenv('APP_VERSION', '1.0.0')

# Sentry configuration for error tracking
SENTRY_DSN = os.getenv('SENTRY_DSN', None)

# Performance monitoring thresholds
SLOW_REQUEST_THRESHOLD = int(os.getenv('SLOW_REQUEST_THRESHOLD', '1000'))  # milliseconds
SLOW_QUERY_THRESHOLD = int(os.getenv('SLOW_QUERY_THRESHOLD', '100'))      # milliseconds

# Initialize logging system
from .logging_config import setup_logging
setup_logging(debug=DEBUG, sentry_dsn=SENTRY_DSN)

# Sentry configuration (if DSN is provided)
if SENTRY_DSN:
    from backend.sentry_config import setup_sentry
    setup_sentry(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        debug=DEBUG,
        sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1'))
    )

# Security settings for production
if not DEBUG:
    # HTTPS settings
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Security headers
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Cookie security
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True  # Safe for JWT-only API; adjust if frontend needs CSRF token access
    
    # Trust proxy (adjust domain for production)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    CSRF_TRUSTED_ORIGINS = [
        origin.strip() 
        for origin in os.getenv('CSRF_TRUSTED_ORIGINS', 'https://localhost:3000').split(',') 
        if origin.strip()
    ]
    
    # Tighten CORS for production
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        origin.strip() 
        for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') 
        if origin.strip()
    ]
    
    # Static files via WhiteNoise (hashed manifest), except during tests/CI
    if not (os.getenv('TESTING') or os.getenv('CI') or DJANGO_ENVIRONMENT == 'testing'):
        STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"

    # Database connection pooling for production
    DATABASES['default']['CONN_MAX_AGE'] = 60
    # Do not set unsupported driver-specific DSN options like MAX_CONNS for psycopg2

# --- PostgreSQL-specific optimizations ---
# All environments now use PostgreSQL only

# Logging-specific settings
LOGGING_CONFIG = None  # Disable Django's default logging config

# Email settings for admin notifications
if not DEBUG:
    ADMINS = [
        (name.strip(), email.strip()) 
        for admin in os.getenv('DJANGO_ADMINS', '').split(',')
        if admin.strip() and '@' in admin
        for name, email in [admin.strip().split(':')]
    ]
    
    MANAGERS = ADMINS
    
    # Email backend for error notifications - using global email config above

# ============================================================================
# JWT CONFIGURATION
# ============================================================================
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),  # Shorter for better security
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.getenv('JWT_SIGNING_KEY', SECRET_KEY),  # Separate JWT key for rotation
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': 'aristay-app',
    'JSON_ENCODER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}

# ============================================================================
# AXES CONFIGURATION (Login Attempt Monitoring)
# ============================================================================
AXES_ENABLED = True

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # AxesStandaloneBackend should be the first backend
    'django.contrib.auth.backends.ModelBackend',  # Django's default backend
]

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=30)
AXES_LOCKOUT_TEMPLATE = 'auth/account_locked.html'
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]  # Updated from deprecated AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP
AXES_IPWARE_META_PRECEDENCE_ORDER = ('HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR')
AXES_NEVER_LOCKOUT_WHITELIST = os.getenv('AXES_WHITELIST', '').split(',') if os.getenv('AXES_WHITELIST') else []

# ============================================================================
# RATE LIMITING CONFIGURATION (consolidated)  
# ============================================================================
# Rate limiting settings moved below with cache configuration

# Cache configuration for production
# Use local memory cache for development, testing, and CI
if DEBUG or os.getenv('CI') or os.getenv('TESTING'):
    # Use local memory cache for development and testing
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': os.getenv('LOC_MEM_CACHE_LOCATION', 'aristay-backend-dev-cache'),
        }
    }
else:
    _redis_url = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
    _use_ssl = os.getenv('REDIS_USE_SSL', 'true').lower() == 'true' or _redis_url.startswith('rediss://')
    _ssl_cert_reqs_env = os.getenv('REDIS_SSL_CERT_REQS', 'required').lower()
    _ssl_cert_reqs = (
        ssl.CERT_NONE if _ssl_cert_reqs_env in ('none', 'false', '0') else ssl.CERT_REQUIRED
    )
    _ssl_ca_path = os.getenv('REDIS_SSL_CA_CERTS')
    _ignore_exceptions = os.getenv('REDIS_IGNORE_EXCEPTIONS', 'true').lower() == 'true'

    _options = {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        'CONNECTION_POOL_KWARGS': {
            'max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS', '50')),
            'retry_on_timeout': True,
        },
    }
    if _use_ssl:
        _ssl_opts = {'ssl_cert_reqs': _ssl_cert_reqs}
        if _ssl_ca_path:
            _ssl_opts['ca_certs'] = _ssl_ca_path
        _options['SSL'] = _ssl_opts
    if _ignore_exceptions:
        _options['IGNORE_EXCEPTIONS'] = True  # prevent cache outages from causing 500s

    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': _redis_url,
            'OPTIONS': _options,
            'TIMEOUT': int(os.getenv('CACHE_TIMEOUT', '300')),  # 5 minutes default
        }
    }

# Rate limiting settings (unused - using DRF throttling instead)
# RATELIMIT_ENABLE = not DEBUG
# RATELIMIT_USE_CACHE = 'default'

# ============================================================================
# UNIFIED LOGIN CONFIGURATION
# ============================================================================

# Redirect users to unified login/logout
LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = '/login/'
LOGIN_REDIRECT_URL = '/login/'  # Will be overridden by our custom logic