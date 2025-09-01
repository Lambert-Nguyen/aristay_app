"""
Custom logging formatters for structured logging
"""
import json
import logging
import traceback
from datetime import datetime
from django.conf import settings
from django.utils import timezone
import pytz


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter that outputs structured logs
    Perfect for production monitoring and log aggregation systems
    """
    
    def format(self, record):
        """Format the log record as JSON"""
        # Base log data
        # Always use Tampa, FL timezone for consistency
        tampa_tz = pytz.timezone('America/New_York')
        now = timezone.now().astimezone(tampa_tz)
        
        log_data = {
            'timestamp': now.isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process': record.process,
            'thread': record.thread,
            'thread_name': record.threadName,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'message'
            ]:
                extra_fields[key] = value
        
        if extra_fields:
            log_data['extra'] = extra_fields
        
        # Add environment information
        log_data['environment'] = {
            'debug': getattr(settings, 'DEBUG', False),
            'service': 'aristay-backend',
            'version': getattr(settings, 'VERSION', '1.0.0'),
        }
        
        # Add request information if available
        if hasattr(record, 'request'):
            request = record.request
            # Check if this is actually a Django request object (not a socket)
            if hasattr(request, 'META') and hasattr(request, 'method'):
                log_data['request'] = {
                    'method': getattr(request, 'method', None),
                    'path': getattr(request, 'path', None),
                    'user_id': getattr(getattr(request, 'user', None), 'id', None),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'remote_addr': self._get_client_ip(request),
                    'content_type': request.META.get('CONTENT_TYPE', ''),
                }
            else:
                # Handle non-Django request objects (like sockets)
                log_data['request'] = {
                    'type': str(type(request).__name__),
                    'note': 'Non-Django request object'
                }
        
        # Add performance metrics if available
        if hasattr(record, 'duration'):
            log_data['performance'] = {
                'duration_ms': record.duration,
                'slow_query': record.duration > 1000,  # Flag slow operations
            }
        
        return json.dumps(log_data, default=str, ensure_ascii=False)
    
    def _get_client_ip(self, request):
        """Get the real client IP address"""
        # Check if request has META attribute (Django request)
        if not hasattr(request, 'META'):
            return 'unknown'
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'


class SecurityFormatter(JSONFormatter):
    """
    Specialized formatter for security-related logs
    Adds security context and sanitizes sensitive data
    """
    
    def format(self, record):
        # Get base JSON format
        log_data = json.loads(super().format(record))
        
        # Add security context
        log_data['security'] = {
            'event_type': getattr(record, 'security_event', 'unknown'),
            'severity': self._get_security_severity(record.levelname),
            'category': getattr(record, 'security_category', 'general'),
        }
        
        # Sanitize sensitive data
        if 'extra' in log_data:
            log_data['extra'] = self._sanitize_data(log_data['extra'])
        
        if 'request' in log_data and 'user_agent' in log_data['request']:
            # Keep user agent but truncate if too long
            ua = log_data['request']['user_agent']
            log_data['request']['user_agent'] = ua[:200] if len(ua) > 200 else ua
        
        return json.dumps(log_data, default=str, ensure_ascii=False)
    
    def _get_security_severity(self, level):
        """Map log level to security severity"""
        mapping = {
            'DEBUG': 'low',
            'INFO': 'low',
            'WARNING': 'medium',
            'ERROR': 'high',
            'CRITICAL': 'critical',
        }
        return mapping.get(level, 'unknown')
    
    def _sanitize_data(self, data):
        """Remove or mask sensitive data"""
        if not isinstance(data, dict):
            return data
        
        sensitive_keys = {
            'password', 'token', 'secret', 'key', 'authorization',
            'cookie', 'session', 'csrf', 'api_key', 'auth_token'
        }
        
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value
        
        return sanitized


class PerformanceFormatter(JSONFormatter):
    """
    Specialized formatter for performance logs
    Adds performance metrics and timing information
    """
    
    def format(self, record):
        # Get base JSON format
        log_data = json.loads(super().format(record))
        
        # Add performance-specific fields
        if hasattr(record, 'duration'):
            log_data['performance'] = {
                'duration_ms': record.duration,
                'category': self._categorize_performance(record.duration),
                'slow_threshold_exceeded': record.duration > 1000,
            }
        
        # Add database query information if available
        if hasattr(record, 'queries_count'):
            log_data['database'] = {
                'queries_count': record.queries_count,
                'queries_time': getattr(record, 'queries_time', 0),
                'slow_queries': getattr(record, 'slow_queries', []),
            }
        
        # Add memory usage if available
        if hasattr(record, 'memory_usage'):
            log_data['memory'] = {
                'usage_mb': record.memory_usage,
                'peak_mb': getattr(record, 'peak_memory', 0),
            }
        
        return json.dumps(log_data, default=str, ensure_ascii=False)
    
    def _categorize_performance(self, duration_ms):
        """Categorize performance based on duration"""
        if duration_ms < 100:
            return 'fast'
        elif duration_ms < 500:
            return 'normal'
        elif duration_ms < 1000:
            return 'slow'
        else:
            return 'very_slow'
