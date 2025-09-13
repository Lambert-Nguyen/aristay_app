"""
System Metrics Collection for AriStay Admin Dashboard
Provides performance, logging, and health metrics for superuser monitoring.
"""

import os
import sys
import time
import psutil
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, Q

from .models import Task, Property, Notification, Profile

logger = logging.getLogger('api.metrics')


class SystemMetrics:
    """Collects and provides system performance and health metrics."""
    
    def __init__(self):
        self.start_time = time.time()
    
    def get_all_metrics(self):
        """Get comprehensive system metrics."""
        try:
            return {
                'system_info': self.get_system_info(),
                'performance': self.get_performance_metrics(),
                'database': self.get_database_metrics(),
                'logging': self.get_logging_metrics(),
                'application': self.get_application_metrics(),
                'health_status': self.get_health_status(),
                'user_activity': self.get_user_activity_metrics(),
                'timestamp': timezone.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {
                'error': str(e),
                'timestamp': timezone.now().isoformat(),
            }
    
    def get_system_info(self):
        """Get basic system information."""
        try:
            return {
                'python_version': sys.version.split()[0],
                'django_version': getattr(settings, 'DJANGO_VERSION', 'Unknown'),
                'platform': sys.platform,
                'hostname': os.uname().nodename if hasattr(os, 'uname') else 'Unknown',
                'process_id': os.getpid(),
                'uptime_seconds': time.time() - self.start_time,
                'debug_mode': settings.DEBUG,
                'timezone': str(settings.TIME_ZONE),
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {'error': str(e)}
    
    def get_performance_metrics(self):
        """Get system performance metrics."""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': psutil.cpu_count(),
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
                },
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_percent': memory.percent,
                    'process_mb': round(process_memory.rss / (1024**2), 2),
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'used_percent': round((disk.used / disk.total) * 100, 2),
                },
                'network': self._get_network_stats(),
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}
    
    def _get_network_stats(self):
        """Get network statistics."""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_received': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_received': net_io.packets_recv,
            }
        except:
            return None
    
    def get_database_metrics(self):
        """Get database performance metrics."""
        try:
            # Connection info
            db_vendor = connection.vendor
            
            # Query counts
            queries_count = len(connection.queries) if settings.DEBUG else 0
            
            # Table sizes (simplified)
            table_counts = {
                'users': User.objects.count(),
                'tasks': Task.objects.count(),
                'properties': Property.objects.count(),
                'notifications': Notification.objects.count(),
                'profiles': Profile.objects.count(),
            }
            
            # Recent activity
            now = timezone.now()
            today = now.date()
            
            recent_activity = {
                'tasks_created_today': Task.objects.filter(created_at__date=today).count(),
                'users_active_today': User.objects.filter(last_login__date=today).count(),
                'notifications_sent_today': Notification.objects.filter(timestamp__date=today).count(),
            }
            
            return {
                'vendor': db_vendor,
                'queries_count': queries_count,
                'table_counts': table_counts,
                'recent_activity': recent_activity,
                'connection_status': 'connected' if connection.connection else 'disconnected',
            }
        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            return {'error': str(e)}
    
    def get_logging_metrics(self):
        """Get logging activity metrics."""
        try:
            log_dir = os.path.join(settings.BASE_DIR, 'logs')
            log_files = {}
            
            if os.path.exists(log_dir):
                for log_file in os.listdir(log_dir):
                    if log_file.endswith('.log'):
                        file_path = os.path.join(log_dir, log_file)
                        try:
                            stat = os.stat(file_path)
                            log_files[log_file] = {
                                'size_mb': round(stat.st_size / (1024**2), 2),
                                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'lines': self._count_file_lines(file_path),
                            }
                        except:
                            log_files[log_file] = {'error': 'Could not read file'}
            
            # Recent log levels from memory (if available)
            log_levels = self._get_recent_log_levels()
            
            return {
                'log_files': log_files,
                'log_directory': log_dir,
                'recent_log_levels': log_levels,
                'logging_configured': bool(settings.LOGGING),
            }
        except Exception as e:
            logger.error(f"Error getting logging metrics: {e}")
            return {'error': str(e)}
    
    def _count_file_lines(self, file_path, max_lines=1000):
        """Count lines in a log file (limited for performance)."""
        try:
            with open(file_path, 'r') as f:
                count = 0
                for _ in f:
                    count += 1
                    if count >= max_lines:
                        return f"{max_lines}+"
                return count
        except:
            return 0
    
    def _get_recent_log_levels(self):
        """Get recent log levels from cache or estimate."""
        try:
            # Try to get from cache (would need to be set by logging handlers)
            cached_levels = cache.get('recent_log_levels', {})
            if cached_levels:
                return cached_levels
            
            # Fallback: estimate from recent log files
            return {
                'info': 'Unknown',
                'warning': 'Unknown', 
                'error': 'Unknown',
                'debug': 'Unknown',
            }
        except:
            return {}
    
    def get_application_metrics(self):
        """Get application-specific metrics."""
        try:
            now = timezone.now()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            
            return {
                'task_metrics': {
                    'total': Task.objects.count(),
                    'pending': Task.objects.filter(status='pending').count(),
                    'in_progress': Task.objects.filter(status='in_progress').count(),
                    'completed': Task.objects.filter(status='completed').count(),
                    'created_24h': Task.objects.filter(created_at__gte=last_24h).count(),
                    'overdue': Task.objects.filter(
                        due_date__lt=now, 
                        status__in=['pending', 'in_progress']
                    ).count(),
                },
                'user_metrics': {
                    'total': User.objects.count(),
                    'active': User.objects.filter(is_active=True).count(),
                    'staff': User.objects.filter(profile__role='staff').count(),
                    'managers': User.objects.filter(profile__role='manager').count(),
                    'superusers': User.objects.filter(is_superuser=True).count(),
                    'logged_in_24h': User.objects.filter(last_login__gte=last_24h).count(),
                    'with_profiles': Profile.objects.count(),
                },
                'property_metrics': {
                    'total': Property.objects.count(),
                },
                'notification_metrics': {
                    'total': Notification.objects.count(),
                    'sent_24h': Notification.objects.filter(timestamp__gte=last_24h).count(),
                    'unread': Notification.objects.filter(read_at__isnull=True).count(),
                },
            }
        except Exception as e:
            logger.error(f"Error getting application metrics: {e}")
            return {'error': str(e)}
    
    def get_health_status(self):
        """Get overall system health status."""
        try:
            health_checks = {
                'database': self._check_database_health(),
                'cache': self._check_cache_health(),
                'disk_space': self._check_disk_space(),
                'memory': self._check_memory_usage(),
                'logging': self._check_logging_health(),
            }
            
            # Overall status
            failed_checks = [name for name, status in health_checks.items() if not status['healthy']]
            overall_status = 'healthy' if not failed_checks else 'warning' if len(failed_checks) < 3 else 'critical'
            
            return {
                'overall_status': overall_status,
                'failed_checks': failed_checks,
                'checks': health_checks,
                'last_check': timezone.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {'error': str(e)}
    
    def _check_database_health(self):
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            User.objects.count()  # Simple query
            query_time = time.time() - start_time
            
            return {
                'healthy': query_time < 1.0,  # Less than 1 second
                'response_time_ms': round(query_time * 1000, 2),
                'status': 'connected',
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'status': 'disconnected',
            }
    
    def _check_cache_health(self):
        """Check cache system health."""
        try:
            test_key = 'health_check_test'
            cache.set(test_key, 'test_value', 30)
            result = cache.get(test_key)
            cache.delete(test_key)
            
            return {
                'healthy': result == 'test_value',
                'status': 'operational' if result == 'test_value' else 'failed',
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'status': 'unavailable',
            }
    
    def _check_disk_space(self):
        """Check available disk space."""
        try:
            disk = psutil.disk_usage('/')
            used_percent = (disk.used / disk.total) * 100
            
            return {
                'healthy': used_percent < 90,  # Less than 90% used
                'used_percent': round(used_percent, 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'status': 'ok' if used_percent < 90 else 'warning' if used_percent < 95 else 'critical',
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'status': 'unknown',
            }
    
    def _check_memory_usage(self):
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            
            return {
                'healthy': memory.percent < 85,  # Less than 85% used
                'used_percent': memory.percent,
                'available_gb': round(memory.available / (1024**3), 2),
                'status': 'ok' if memory.percent < 85 else 'warning' if memory.percent < 95 else 'critical',
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'status': 'unknown',
            }
    
    def _check_logging_health(self):
        """Check logging system health."""
        try:
            log_dir = os.path.join(settings.BASE_DIR, 'logs')
            
            if not os.path.exists(log_dir):
                return {
                    'healthy': False,
                    'error': 'Log directory does not exist',
                    'status': 'missing',
                }
            
            # Check if we can write to log directory
            test_file = os.path.join(log_dir, 'health_test.tmp')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                writable = True
            except:
                writable = False
            
            return {
                'healthy': writable,
                'status': 'writable' if writable else 'read_only',
                'log_directory': log_dir,
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'status': 'error',
            }
    
    def get_user_activity_metrics(self):
        """Get user activity and engagement metrics."""
        try:
            now = timezone.now()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            last_30d = now - timedelta(days=30)
            
            return {
                'login_activity': {
                    'last_24h': User.objects.filter(last_login__gte=last_24h).count(),
                    'last_7d': User.objects.filter(last_login__gte=last_7d).count(),
                    'last_30d': User.objects.filter(last_login__gte=last_30d).count(),
                },
                'task_activity': {
                    'created_24h': Task.objects.filter(created_at__gte=last_24h).count(),
                    'completed_24h': Task.objects.filter(
                        modified_at__gte=last_24h, 
                        status='completed'
                    ).count(),
                },
                'role_distribution': self._get_role_distribution(),
                'most_active_users': self._get_most_active_users(),
            }
        except Exception as e:
            logger.error(f"Error getting user activity metrics: {e}")
            return {'error': str(e)}
    
    def _get_role_distribution(self):
        """Get distribution of user roles."""
        try:
            return Profile.objects.values('role').annotate(count=Count('role')).order_by('-count')
        except:
            return []
    
    def _get_most_active_users(self, limit=5):
        """Get most active users by task assignments."""
        try:
            return list(
                User.objects.annotate(
                    task_count=Count('assigned_tasks')
                ).filter(
                    task_count__gt=0
                ).order_by('-task_count')[:limit].values(
                    'username', 'first_name', 'last_name', 'task_count'
                )
            )
        except:
            return []


def get_system_metrics():
    """Convenience function to get all system metrics."""
    metrics_collector = SystemMetrics()
    return metrics_collector.get_all_metrics()
