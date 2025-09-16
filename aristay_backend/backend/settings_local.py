"""
Local Development Settings
Use this for local development with PostgreSQL
"""

from .settings_base import *

# Using Django's default User model
# AUTH_USER_MODEL = 'auth.User'  # This is the default

# Local development settings - uses your existing .env structure
DJANGO_ENVIRONMENT = "development"

# Override specific settings for local development
DEBUG = True
SECURE_SSL_REDIRECT = False

# Use your existing .env variables
SECRET_KEY = os.getenv('SECRET_KEY', 'local-dev-secret-key-change-me')
JWT_SIGNING_KEY = os.getenv('JWT_SIGNING_KEY', 'local-jwt-key-change-me')

# CORS settings from your .env
CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'true').lower() == 'true'
CORS_ALLOWED_ORIGINS = [
    origin.strip() 
    for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',') 
    if origin.strip()
]

# Frontend URL from your .env
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Email settings from your .env
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '1025'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'false').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Cloudinary settings from your .env
USE_CLOUDINARY = os.getenv('USE_CLOUDINARY', 'true').lower() == 'true'
if USE_CLOUDINARY:
    CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')
    if CLOUDINARY_URL:
        # Parse CLOUDINARY_URL if provided
        import cloudinary
        cloudinary.config(cloudinary_url=CLOUDINARY_URL)
    else:
        # Use individual environment variables
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

# Redis configuration from your .env (optional)
REDIS_URL = os.getenv('REDIS_URL')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }

print("🔧 Using local development settings with PostgreSQL")
