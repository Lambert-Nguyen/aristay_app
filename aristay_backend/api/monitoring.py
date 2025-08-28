"""
System monitoring and health check endpoints
"""
import logging
import time
import os
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import connection
from django.conf import settings
from django.core.cache import cache
from django.contrib.admin.views.decorators import staff_member_required
from api.models import Task, User, Notification


logger = logging.getLogger('api')


class HealthCheckView(View):
    """
    Basic health check endpoint for load balancers and monitoring
    Returns 200 OK if the service is healthy
    """
    
    def get(self, request):
        """Simple health check"""
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Test cache
            cache.set('health_check', 'ok', 10)
            cache_result = cache.get('health_check')
            
            if cache_result != 'ok':
                raise Exception("Cache test failed")
            
            return JsonResponse({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'aristay-backend',
                'version': getattr(settings, 'VERSION', '1.0.0'),
            })
        
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
            }, status=503)


@method_decorator(staff_member_required, name='dispatch')
class DetailedHealthCheckView(View):
    """
    Detailed health check for administrators
    Includes system metrics, database status, and performance indicators
    """
    
    def get(self, request):
        """Comprehensive health check"""
        start_time = time.time()
        
        try:
            health_data = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'aristay-backend',
                'version': getattr(settings, 'VERSION', '1.0.0'),
                'environment': getattr(settings, 'ENVIRONMENT', 'unknown'),
                'debug_mode': settings.DEBUG,
                'checks': {},
                'metrics': {},
            }
            
            # Database health
            health_data['checks']['database'] = self._check_database()
            
            # Cache health
            health_data['checks']['cache'] = self._check_cache()
            
            # File system health
            health_data['checks']['filesystem'] = self._check_filesystem()
            
            # System metrics
            health_data['metrics']['system'] = self._get_system_metrics()
            
            # Application metrics
            health_data['metrics']['application'] = self._get_app_metrics()
            
            # Log analysis
            health_data['metrics']['logs'] = self._get_log_metrics()
            
            # Performance metrics
            health_data['metrics']['performance'] = {
                'health_check_duration_ms': (time.time() - start_time) * 1000
            }
            
            # Determine overall health
            failed_checks = [name for name, check in health_data['checks'].items() if not check['healthy']]
            if failed_checks:
                health_data['status'] = 'degraded'
                health_data['failed_checks'] = failed_checks
                status_code = 207  # Multi-Status
            else:
                status_code = 200
            
            return JsonResponse(health_data, status=status_code)
        
        except Exception as e:
            logger.error(f"Detailed health check failed: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
            }, status=500)
    
    def _check_database(self):
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test basic connectivity
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Test a simple query
            task_count = Task.objects.count()
            
            duration = (time.time() - start_time) * 1000
            
            return {
                'healthy': True,
                'duration_ms': duration,
                'task_count': task_count,
                'slow_query': duration > 100,
            }
        
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
            }
    
    def _check_cache(self):
        """Check cache connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test set/get operations
            test_key = f'health_check_{int(time.time())}'
            test_value = 'health_test'
            
            cache.set(test_key, test_value, 10)
            retrieved_value = cache.get(test_key)
            cache.delete(test_key)
            
            duration = (time.time() - start_time) * 1000
            
            if retrieved_value != test_value:
                raise Exception("Cache value mismatch")
            
            return {
                'healthy': True,
                'duration_ms': duration,
                'slow_operation': duration > 50,
            }
        
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
            }
    
    def _check_filesystem(self):
        """Check file system health"""
        try:
            # Check logs directory
            logs_dir = Path(settings.BASE_DIR) / 'logs'
            logs_exist = logs_dir.exists()
            logs_writable = os.access(logs_dir, os.W_OK) if logs_exist else False
            
            # Check media directory
            media_dir = Path(settings.MEDIA_ROOT) if hasattr(settings, 'MEDIA_ROOT') else None
            media_exist = media_dir.exists() if media_dir else False
            media_writable = os.access(media_dir, os.W_OK) if media_exist else False
            
            # Check disk space
            disk_usage = psutil.disk_usage('/')
            disk_free_percent = (disk_usage.free / disk_usage.total) * 100
            
            return {
                'healthy': logs_writable and (not media_dir or media_writable) and disk_free_percent > 5,
                'logs_directory': {
                    'exists': logs_exist,
                    'writable': logs_writable,
                    'path': str(logs_dir),
                },
                'media_directory': {
                    'exists': media_exist,
                    'writable': media_writable,
                    'path': str(media_dir) if media_dir else None,
                },
                'disk_space': {
                    'free_percent': round(disk_free_percent, 2),
                    'free_gb': round(disk_usage.free / (1024**3), 2),
                    'total_gb': round(disk_usage.total / (1024**3), 2),
                    'low_space_warning': disk_free_percent < 10,
                },
            }
        
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
            }
    
    def _get_system_metrics(self):
        """Get system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Process metrics
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info()
            
            return {
                'cpu': {
                    'usage_percent': cpu_percent,
                    'cores': cpu_count,
                    'high_usage': cpu_percent > 80,
                },
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'usage_percent': memory.percent,
                    'high_usage': memory.percent > 85,
                },
                'process': {
                    'memory_mb': round(process_memory.rss / (1024**2), 2),
                    'threads': process.num_threads(),
                    'connections': len(process.connections()) if hasattr(process, 'connections') else 0,
                },
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def _get_app_metrics(self):
        """Get application-specific metrics"""
        try:
            now = datetime.now()
            last_hour = now - timedelta(hours=1)
            last_day = now - timedelta(days=1)
            
            # Task metrics
            total_tasks = Task.objects.count()
            recent_tasks = Task.objects.filter(created_at__gte=last_hour).count()
            overdue_tasks = Task.objects.filter(
                due_date__lt=now,
                status__in=['pending', 'in-progress']
            ).count()
            
            # User metrics
            total_users = User.objects.count()
            active_users = User.objects.filter(last_login__gte=last_day).count()
            
            # Notification metrics
            unread_notifications = Notification.objects.filter(read=False).count()
            recent_notifications = Notification.objects.filter(timestamp__gte=last_hour).count()
            
            return {
                'tasks': {
                    'total': total_tasks,
                    'recent_hour': recent_tasks,
                    'overdue': overdue_tasks,
                    'overdue_ratio': round(overdue_tasks / max(total_tasks, 1), 3),
                },
                'users': {
                    'total': total_users,
                    'active_24h': active_users,
                    'activity_ratio': round(active_users / max(total_users, 1), 3),
                },
                'notifications': {
                    'unread': unread_notifications,
                    'recent_hour': recent_notifications,
                },
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def _get_log_metrics(self):
        """Analyze recent log files"""
        try:
            logs_dir = Path(settings.BASE_DIR) / 'logs'
            if not logs_dir.exists():
                return {'error': 'Logs directory not found'}
            
            metrics = {}
            
            # Analyze error log
            error_log = logs_dir / 'error.log'
            if error_log.exists():
                metrics['error_log'] = self._analyze_log_file(error_log, 'ERROR')
            
            # Analyze info log
            info_log = logs_dir / 'info.log'
            if info_log.exists():
                metrics['info_log'] = self._analyze_log_file(info_log, 'INFO')
            
            # Analyze performance log
            perf_log = logs_dir / 'performance.log'
            if perf_log.exists():
                metrics['performance_log'] = self._analyze_log_file(perf_log, 'INFO')
            
            return metrics
        
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_log_file(self, log_file, min_level='INFO'):
        """Analyze a single log file"""
        try:
            stat = log_file.stat()
            size_mb = stat.st_size / (1024 * 1024)
            
            # Count recent entries (last 1000 lines)
            recent_lines = []
            with open(log_file, 'r', errors='ignore') as f:
                # Read last 1000 lines efficiently
                lines = f.readlines()
                recent_lines = lines[-1000:] if len(lines) > 1000 else lines
            
            # Count log levels in recent entries
            error_count = sum(1 for line in recent_lines if '"level": "ERROR"' in line)
            warning_count = sum(1 for line in recent_lines if '"level": "WARNING"' in line)
            
            return {
                'size_mb': round(size_mb, 2),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'recent_entries': len(recent_lines),
                'recent_errors': error_count,
                'recent_warnings': warning_count,
                'large_file': size_mb > 100,
                'high_error_rate': error_count > 10,
            }
        
        except Exception as e:
            return {'error': str(e)}


@csrf_exempt
def log_client_error(request):
    """
    Endpoint for frontend to report client-side errors
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        
        # Log the client error
        logger.error(
            f"Client error: {data.get('message', 'Unknown error')}",
            extra={
                'client_error': True,
                'error_type': data.get('type', 'unknown'),
                'stack_trace': data.get('stack', ''),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'url': data.get('url', ''),
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                'timestamp': data.get('timestamp', ''),
                'additional_data': data.get('extra', {}),
            }
        )
        
        return JsonResponse({'status': 'logged'})
    
    except Exception as e:
        logger.error(f"Failed to log client error: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Failed to log error'}, status=500)
