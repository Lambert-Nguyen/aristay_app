"""
Production-ready logging configuration for AriStay backend
Provides structured JSON logging with rotation, different log levels, and Sentry integration
"""
import os
import sys
from pathlib import Path
from logging.config import dictConfig

# Base directory for logs
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / 'logs'

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)

def get_logging_config(debug=False, sentry_dsn=None):
    """
    Get logging configuration based on environment
    
    Args:
        debug (bool): Whether running in debug mode
        sentry_dsn (str): Sentry DSN for error tracking
    """
    
    # Log levels based on environment
    root_level = 'DEBUG' if debug else 'INFO'
    django_level = 'INFO' if debug else 'WARNING'
    
    config = {
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
            'json': {
                '()': 'backend.formatters.JSONFormatter',
            },
            'console': {
                'format': '\033[1;32m{asctime}\033[0m \033[1;35m{name}\033[0m \033[1;36m{levelname}\033[0m {message}',
                'style': '{',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            },
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG' if debug else 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'console',
                'stream': sys.stdout,
            },
            'file_debug': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGS_DIR / 'debug.log',
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 5,
                'formatter': 'json',
                'filters': ['require_debug_true'],
            },
            'file_info': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGS_DIR / 'info.log',
                'maxBytes': 100 * 1024 * 1024,  # 100MB
                'backupCount': 10,
                'formatter': 'json',
            },
            'file_error': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGS_DIR / 'error.log',
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 20,  # Keep more error logs
                'formatter': 'json',
            },
            'file_security': {
                'level': 'WARNING',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGS_DIR / 'security.log',
                'maxBytes': 25 * 1024 * 1024,  # 25MB
                'backupCount': 15,
                'formatter': 'json',
            },
            'file_performance': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGS_DIR / 'performance.log',
                'maxBytes': 100 * 1024 * 1024,  # 100MB
                'backupCount': 7,  # Weekly rotation
                'formatter': 'json',
            },
            'mail_admins': {
                'level': 'ERROR',
                'class': 'django.utils.log.AdminEmailHandler',
                'filters': ['require_debug_false'],
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file_info', 'file_error'],
                'level': django_level,
                'propagate': False,
            },
            'django.request': {
                'handlers': ['file_error', 'mail_admins'],
                'level': 'ERROR',
                'propagate': False,
            },
            'django.security': {
                'handlers': ['file_security', 'mail_admins'],
                'level': 'WARNING',
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': ['file_debug'] if debug else [],
                'level': 'DEBUG' if debug else 'WARNING',
                'propagate': False,
            },
            'api': {
                'handlers': ['console', 'file_info', 'file_error'],
                'level': 'DEBUG' if debug else 'INFO',
                'propagate': False,
            },
            'api.performance': {
                'handlers': ['file_performance'],
                'level': 'INFO',
                'propagate': False,
            },
            'api.security': {
                'handlers': ['file_security'],
                'level': 'WARNING',
                'propagate': False,
            },
            'api.tasks': {
                'handlers': ['console', 'file_info'],
                'level': 'INFO',
                'propagate': False,
            },
            'api.notifications': {
                'handlers': ['console', 'file_info'],
                'level': 'INFO',
                'propagate': False,
            },
            'celery': {
                'handlers': ['console', 'file_info', 'file_error'],
                'level': 'INFO',
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console', 'file_info', 'file_error'],
            'level': root_level,
        },
    }
    
    # Add Sentry handler if DSN is provided
    if sentry_dsn:
        config['handlers']['sentry'] = {
            'level': 'ERROR',
            '()': 'sentry_sdk.integrations.logging.SentryHandler',
        }
        # Add sentry to root and api loggers
        config['loggers']['api']['handlers'].append('sentry')
        config['root']['handlers'].append('sentry')
    
    return config

def setup_logging(debug=False, sentry_dsn=None):
    """Setup logging with the given configuration"""
    config = get_logging_config(debug=debug, sentry_dsn=sentry_dsn)
    dictConfig(config)
    
    # Log that logging has been configured
    import logging
    logger = logging.getLogger('api')
    logger.info(
        "Logging system initialized",
        extra={
            'debug_mode': debug,
            'sentry_enabled': bool(sentry_dsn),
            'logs_directory': str(LOGS_DIR),
        }
    )
