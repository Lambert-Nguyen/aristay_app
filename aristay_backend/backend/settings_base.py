"""
Base Django settings for Aristay project.
Contains common settings shared across all environments.
"""

import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Optional local .env loading for development ---
if os.getenv("LOAD_DOTENV", "true").lower() == "true":
    try:
        from dotenv import load_dotenv
        for _candidate in [(BASE_DIR / ".env"), (BASE_DIR.parent / ".env")]:
            if _candidate.exists():
                load_dotenv(_candidate)
                break
    except ImportError:
        pass

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

# Application definition
DJANGO_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',  # Admin must come after auth and contenttypes
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework.authtoken',  # For Token authentication
    'corsheaders',
    'axes',
    'django_extensions',
]

LOCAL_APPS = [
    'api',
]

USE_CLOUDINARY = os.getenv('USE_CLOUDINARY', 'false').lower() == 'true'
if USE_CLOUDINARY:
    THIRD_PARTY_APPS += ['cloudinary', 'cloudinary_storage']

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Add CORS middleware near top
    'axes.middleware.AxesMiddleware',  # before AuthenticationMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # Django's auth middleware must run before you try to use request.user
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Admin access control middleware (must run after authentication)
    'backend.middleware.AdminAccessMiddleware',
    # Agent's Phase 2: Audit middleware for request context capture
    'api.audit_middleware.AuditMiddleware',
    # Now your timezone middleware can safely reference request.user
    'backend.middleware.TimezoneMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'backend.memory_middleware.MemoryManagementMiddleware',  # Memory management
    # Production logging and monitoring middleware
    'backend.middleware.RequestLoggingMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'api' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
# Prefer lightweight SQLite during tests to avoid Postgres-specific constraints
if os.getenv('DJANGO_ENVIRONMENT', '').lower() == 'testing':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            'OPTIONS': {
                'timeout': 20,
            }
        }
    }
else:
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/aristay_local')
    # Only use dj_database_url if DATABASE_URL is not empty
    if DATABASE_URL and DATABASE_URL.strip():
        DATABASES = {
            'default': dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=60,
                conn_health_checks=True,
            )
        }
    else:
        # Fallback to default PostgreSQL configuration
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'aristay_local',
                'USER': 'postgres',
                'PASSWORD': 'postgres',
                'HOST': '127.0.0.1',
                'PORT': '5432',
                'CONN_MAX_AGE': 60,
            }
        }

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'  # Tampa, FL timezone
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/min',
        'token_refresh': '2/min',
        'evidence_upload': '10/min',
        'taskimage': '20/min',
    },
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.getenv('JWT_SIGNING_KEY', SECRET_KEY),
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS settings
CORS_ALLOWED_ORIGINS = []
CORS_ALLOW_CREDENTIALS = True

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Axes settings
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # 1 hour
# AXES_LOCKOUT_CALLABLE = 'axes.lockout.database_lockout'  # This is deprecated
AXES_LOCKOUT_TEMPLATE = 'admin/lockout.html'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # Axes backend must be first
    'django.contrib.auth.backends.ModelBackend',
]

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'debug.log',
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'error.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'api': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'backend': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['error_file'],
        'level': 'ERROR',
    },
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

# Timezone settings
USE_TZ = True
TIME_ZONE = 'America/New_York'  # Tampa, FL timezone

if USE_CLOUDINARY:
    # Cloudinary configuration
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME', ''),
        'API_KEY': os.getenv('CLOUDINARY_API_KEY', ''),
        'API_SECRET': os.getenv('CLOUDINARY_API_SECRET', ''),
    }
    if all([CLOUDINARY_STORAGE['CLOUD_NAME'], CLOUDINARY_STORAGE['API_KEY'], CLOUDINARY_STORAGE['API_SECRET']]):
        cloudinary.config(
            cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
            api_key=CLOUDINARY_STORAGE['API_KEY'],
            api_secret=CLOUDINARY_STORAGE['API_SECRET']
        )

# Storage backend selection
# Expose a simple feature flag used by tests and CI
USE_CLOUDINARY = os.getenv('USE_CLOUDINARY', 'false').lower() == 'true'

# Django 5+ STORAGES setting
if USE_CLOUDINARY:
    STORAGES = {
        'default': {
            'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }
else:
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
            'OPTIONS': {
                'location': str(MEDIA_ROOT),
            },
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }

# In tests/CI, avoid manifest storage entirely to prevent missing-manifest errors
if os.getenv('TESTING') or os.getenv('CI') or os.getenv('DJANGO_ENVIRONMENT', '').lower() == 'testing':
    try:
        STORAGES['staticfiles']['BACKEND'] = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    except Exception:
        STORAGES = {
            **(STORAGES or {}),
            'staticfiles': {
                'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
            },
        }
    # Also force default storage to local filesystem during tests
    STORAGES['default'] = {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    }
