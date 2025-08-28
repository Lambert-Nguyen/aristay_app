"""
Sentry configuration for production error tracking
"""
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.sqlalchemy import SqlAlchemyIntegration
import logging


def setup_sentry(dsn, environment='production', debug=False, sample_rate=1.0):
    """
    Configure Sentry for error tracking and performance monitoring
    
    Args:
        dsn (str): Sentry DSN from your project settings
        environment (str): Environment name (production, staging, development)
        debug (bool): Whether to enable debug mode
        sample_rate (float): Performance monitoring sample rate (0.0 to 1.0)
    """
    
    # Configure logging integration
    logging_integration = LoggingIntegration(
        level=logging.INFO,        # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )
    
    # Configure Django integration
    django_integration = DjangoIntegration(
        transaction_style='url',   # Use URL patterns for transaction names
        middleware_spans=True,     # Instrument middleware
        signals_spans=True,        # Instrument Django signals
        cache_spans=True,          # Instrument cache operations
    )
    
    # Configure Celery integration (if using Celery)
    celery_integration = CeleryIntegration(
        monitor_beat_tasks=True,   # Monitor periodic tasks
        propagate_traces=True,     # Propagate traces across tasks
    )
    
    # Initialize Sentry
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        debug=debug,
        
        # Integrations
        integrations=[
            django_integration,
            logging_integration,
            celery_integration,
            SqlAlchemyIntegration(),
        ],
        
        # Performance Monitoring
        traces_sample_rate=sample_rate,  # Capture performance data
        profiles_sample_rate=0.1,        # Capture profiling data (10%)
        
        # Error Handling
        attach_stacktrace=True,          # Attach stack traces to messages
        send_default_pii=False,          # Don't send personally identifiable info
        max_breadcrumbs=50,              # Keep more breadcrumbs for context
        
        # Custom error filtering
        before_send=filter_sensitive_errors,
        before_send_transaction=filter_sensitive_transactions,
        
        # Release tracking
        release=get_release_version(),
    )
    
    # Log successful Sentry initialization
    logger = logging.getLogger('api')
    logger.info(
        "Sentry error tracking initialized",
        extra={
            'environment': environment,
            'sample_rate': sample_rate,
            'debug_mode': debug,
        }
    )


def filter_sensitive_errors(event, hint):
    """
    Filter out sensitive information from error reports
    """
    # Remove sensitive data from request
    if 'request' in event:
        request = event['request']
        
        # Remove sensitive headers
        if 'headers' in request:
            sensitive_headers = ['authorization', 'cookie', 'x-api-key']
            for header in sensitive_headers:
                if header in request['headers']:
                    request['headers'][header] = '[Filtered]'
        
        # Remove sensitive data from request body
        if 'data' in request and isinstance(request['data'], dict):
            request['data'] = sanitize_dict(request['data'])
    
    # Remove sensitive data from extra context
    if 'extra' in event:
        event['extra'] = sanitize_dict(event['extra'])
    
    # Skip certain types of errors in production
    if 'exception' in event:
        for exception in event['exception']['values']:
            error_type = exception.get('type', '')
            error_value = exception.get('value', '')
            
            # Skip common Django errors that aren't actionable
            if error_type in ['DisallowedHost', 'SuspiciousOperation']:
                return None
            
            # Skip certain permission errors
            if 'permission denied' in error_value.lower():
                return None
    
    return event


def filter_sensitive_transactions(event, hint):
    """
    Filter sensitive information from performance transactions
    """
    # Remove sensitive data from transaction context
    if 'request' in event:
        request = event['request']
        
        # Remove query parameters that might contain sensitive data
        if 'query_string' in request:
            # Keep query string but remove sensitive parameters
            query_string = request['query_string']
            if any(param in query_string for param in ['token', 'key', 'password']):
                request['query_string'] = '[Filtered]'
    
    return event


def sanitize_dict(data):
    """
    Recursively sanitize dictionary data
    """
    if not isinstance(data, dict):
        return data
    
    sensitive_keys = {
        'password', 'token', 'secret', 'key', 'authorization',
        'cookie', 'session', 'csrf', 'api_key', 'auth_token',
        'credit_card', 'ssn', 'social_security'
    }
    
    sanitized = {}
    for key, value in data.items():
        key_lower = str(key).lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = '[Filtered]'
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_dict(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value
    
    return sanitized


def get_release_version():
    """
    Get the current release version for Sentry tracking
    """
    try:
        # Try to get version from git
        import subprocess
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()[:8]  # Short commit hash
    except:
        pass
    
    # Fallback to a default version
    return 'unknown'


def add_user_context(user):
    """
    Add user context to Sentry scope
    Call this after user authentication
    """
    with sentry_sdk.configure_scope() as scope:
        scope.user = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': getattr(user, 'is_staff', False),
            'is_superuser': getattr(user, 'is_superuser', False),
        }


def add_request_context(request):
    """
    Add request context to Sentry scope
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag('request_method', request.method)
        scope.set_tag('request_path', request.path)
        
        # Add custom context
        scope.set_context('request', {
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'remote_addr': get_client_ip(request),
        })


def capture_task_context(task_name, task_args=None, task_kwargs=None):
    """
    Add task context for background tasks
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag('task_name', task_name)
        scope.set_context('task', {
            'name': task_name,
            'args': task_args,
            'kwargs': task_kwargs,
        })


def get_client_ip(request):
    """Get the real client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
