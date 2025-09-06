# api/security_dashboard.py
"""
Security monitoring dashboard and utilities
"""

import logging
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .security_models import SecurityEvent, UserSession, SuspiciousActivity

logger = logging.getLogger('api.security')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def security_dashboard(request):
    """Security monitoring dashboard for administrators"""
    
    # Time periods for analysis
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    # Recent security events
    recent_events = SecurityEvent.objects.order_by('-created_at')[:50]
    
    # Login statistics
    login_stats = {
        'successful_logins_24h': SecurityEvent.objects.filter(
            event_type='login_success',
            created_at__gte=last_24h
        ).count(),
        'failed_logins_24h': SecurityEvent.objects.filter(
            event_type='login_failure',
            created_at__gte=last_24h
        ).count(),
        'successful_logins_7d': SecurityEvent.objects.filter(
            event_type='login_success',
            created_at__gte=last_7d
        ).count(),
        'failed_logins_7d': SecurityEvent.objects.filter(
            event_type='login_failure',
            created_at__gte=last_7d
        ).count(),
    }
    
    # Session statistics
    session_stats = {
        'active_sessions': UserSession.objects.filter(
            is_active=True,
            last_activity__gte=last_24h
        ).count(),
        'total_sessions_24h': UserSession.objects.filter(
            created_at__gte=last_24h
        ).count(),
        'unique_users_24h': UserSession.objects.filter(
            created_at__gte=last_24h
        ).values('user').distinct().count(),
    }
    
    # Security threat analysis
    threat_stats = {
        'suspicious_ips': SuspiciousActivity.objects.filter(
            count__gte=5,
            last_seen__gte=last_24h
        ).count(),
        'blocked_ips': SuspiciousActivity.objects.filter(
            blocked=True
        ).count(),
        'high_severity_events': SecurityEvent.objects.filter(
            severity__in=['high', 'critical'],
            created_at__gte=last_7d
        ).count(),
    }
    
    # Top suspicious IPs
    suspicious_ips = SuspiciousActivity.objects.filter(
        last_seen__gte=last_7d
    ).order_by('-count')[:10]
    
    # Failed login attempts by IP
    failed_login_ips = SecurityEvent.objects.filter(
        event_type='login_failure',
        created_at__gte=last_24h
    ).values('ip_address').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'recent_events': recent_events,
        'login_stats': login_stats,
        'session_stats': session_stats,
        'threat_stats': threat_stats,
        'suspicious_ips': suspicious_ips,
        'failed_login_ips': failed_login_ips,
        'refresh_interval': 30,  # seconds
    }
    
    if request.headers.get('Accept') == 'application/json':
        # Return JSON for AJAX requests
        return JsonResponse({
            'login_stats': login_stats,
            'session_stats': session_stats,
            'threat_stats': threat_stats,
            'recent_events': [
                {
                    'id': event.pk,
                    'event_type': event.event_type,
                    'severity': event.severity,
                    'ip_address': event.ip_address,
                    'user': event.user.username if event.user else None,
                    'created_at': event.created_at.isoformat(),
                    'details': event.details,
                }
                for event in recent_events[:20]
            ],
        })
    
    return render(request, 'admin/security_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def security_events(request):
    """API endpoint for security events"""
    
    # Filters
    event_type = request.GET.get('event_type')
    severity = request.GET.get('severity')
    hours = int(request.GET.get('hours', 24))
    limit = int(request.GET.get('limit', 100))
    
    # Base query
    events = SecurityEvent.objects.all()
    
    # Apply filters
    if event_type:
        events = events.filter(event_type=event_type)
    
    if severity:
        events = events.filter(severity=severity)
    
    if hours:
        since = timezone.now() - timedelta(hours=hours)
        events = events.filter(created_at__gte=since)
    
    # Get events
    events = events.order_by('-created_at')[:limit]
    
    events_data = [
        {
            'id': event.pk,
            'event_type': event.event_type,
            'severity': event.severity,
            'ip_address': event.ip_address,
            'user_agent': event.user_agent[:100] if event.user_agent else '',
            'user': event.user.username if event.user else None,
            'created_at': event.created_at.isoformat(),
            'details': event.details,
            'resolved': event.resolved,
        }
        for event in events
    ]
    
    return JsonResponse({'events': events_data})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def active_sessions(request):
    """API endpoint for active sessions"""
    
    sessions = UserSession.objects.filter(
        is_active=True
    ).select_related('user').order_by('-last_activity')[:100]
    
    sessions_data = [
        {
            'id': session.pk,
            'user': session.user.username,
            'device_type': session.device_type,
            'ip_address': session.ip_address,
            'location': session.location,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'is_expired': session.is_expired,
        }
        for session in sessions
    ]
    
    return JsonResponse({'sessions': sessions_data})


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(['POST'])
def terminate_session(request, session_id):
    """Terminate a specific user session"""
    try:
        session = UserSession.objects.get(id=session_id, is_active=True)
        session.deactivate()
        
        # Log the action
        SecurityEvent.log_event(
            'session_terminated_by_admin',
            request=request,
            user=request.user,
            severity='medium',
            target_user=session.user.username,
            session_id=session_id
        )
        
        logger.info(
            f"Admin {request.user.username} terminated session {session_id} for user {session.user.username}"
        )
        
        return JsonResponse({'success': True, 'message': 'Session terminated'})
    
    except UserSession.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)
    except Exception as e:
        logger.error(f"Failed to terminate session {session_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Failed to terminate session'}, status=500)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def security_analytics(request):
    """Security analytics and trends"""
    
    days = int(request.GET.get('days', 7))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Daily login trends
    daily_stats = []
    current_date = start_date
    
    while current_date <= end_date:
        day_start = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
        day_end = day_start + timedelta(days=1)
        
        successful = SecurityEvent.objects.filter(
            event_type='login_success',
            created_at__range=[day_start, day_end]
        ).count()
        
        failed = SecurityEvent.objects.filter(
            event_type='login_failure',
            created_at__range=[day_start, day_end]
        ).count()
        
        daily_stats.append({
            'date': current_date.isoformat(),
            'successful_logins': successful,
            'failed_logins': failed,
        })
        
        current_date += timedelta(days=1)
    
    # Top users by login frequency
    top_users = SecurityEvent.objects.filter(
        event_type='login_success',
        created_at__gte=timezone.now() - timedelta(days=days)
    ).values('user__username').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Security event distribution
    event_distribution = SecurityEvent.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=days)
    ).values('event_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return JsonResponse({
        'daily_stats': daily_stats,
        'top_users': list(top_users),
        'event_distribution': list(event_distribution),
    })


def check_security_threats():
    """Check for security threats and return alerts"""
    alerts = []
    
    # Check for brute force attempts (more than 10 failures in 5 minutes)
    five_min_ago = timezone.now() - timedelta(minutes=5)
    failed_logins = SecurityEvent.objects.filter(
        event_type='login_failure',
        created_at__gte=five_min_ago
    ).values('ip_address').annotate(count=Count('ip_address'))
    
    for item in failed_logins:
        if item['count'] > 10:
            alerts.append({
                'type': 'brute_force',
                'severity': 'high',
                'message': f"Potential brute force attack from {item['ip_address']} ({item['count']} attempts)",
                'ip_address': item['ip_address'],
            })
    
    # Check for suspicious user agents
    hour_ago = timezone.now() - timedelta(hours=1)
    suspicious_events = SecurityEvent.objects.filter(
        event_type='suspicious_activity',
        created_at__gte=hour_ago
    ).count()
    
    if suspicious_events > 5:
        alerts.append({
            'type': 'suspicious_activity',
            'severity': 'medium',
            'message': f"High number of suspicious requests: {suspicious_events}",
        })
    
    # Check for multiple failed logins from same user
    failed_user_logins = SecurityEvent.objects.filter(
        event_type='login_failure',
        created_at__gte=five_min_ago
    ).values('details__username').annotate(count=Count('id'))
    
    for item in failed_user_logins:
        if item['count'] > 5:
            username = item.get('details__username')
            if username:
                alerts.append({
                    'type': 'account_attack',
                    'severity': 'medium',
                    'message': f"Multiple failed logins for user: {username} ({item['count']} attempts)",
                    'username': username,
                })
    
    return alerts


def send_security_alert(alert):
    """Send security alert to administrators"""
    # Log the alert
    logger.warning(f"Security Alert: {alert['message']}")
    
    # Here you could implement email notifications, Slack webhooks, etc.
    # For now, just create a security event
    SecurityEvent.objects.create(
        event_type='security_alert',
        ip_address='127.0.0.1',
        severity=alert['severity'],
        details=alert
    )
