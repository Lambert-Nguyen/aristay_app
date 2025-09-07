# api/notification_management_views.py
"""
Notification Management Views and UI for Admins/Managers
Provides DRF endpoints and HTML interface for notification management
"""

import logging
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .decorators import staff_or_perm
from .models import Notification, NotificationVerb, Task
from .services.notification_service import NotificationService

logger = logging.getLogger(__name__)


# DRF API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_stats_api(request):
    """
    DRF API endpoint to get notification statistics
    GET /api/notifications/stats/
    """
    if not request.user.is_staff:
        return Response(
            {"error": "Staff permissions required"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Basic stats
    total_notifications = Notification.objects.count()
    recent_notifications = Notification.objects.filter(
        created_at__gte=start_date
    ).count()
    
    unread_notifications = Notification.objects.filter(is_read=False).count()
    
    # Notification breakdown by verb
    verb_stats = list(Notification.objects.values('verb__name').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    # Daily activity (last 7 days)
    daily_stats = []
    for i in range(7):
        date = end_date - timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count = Notification.objects.filter(
            created_at__gte=day_start,
            created_at__lt=day_end
        ).count()
        
        daily_stats.append({
            'date': day_start.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Top users by notifications received
    user_stats = list(
        Notification.objects.filter(recipient__isnull=False)
        .values('recipient__username', 'recipient__first_name', 'recipient__last_name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    return Response({
        "total_notifications": total_notifications,
        "recent_notifications": recent_notifications,
        "unread_notifications": unread_notifications,
        "verb_breakdown": verb_stats,
        "daily_activity": daily_stats,
        "top_users": user_stats
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_test_notification_api(request):
    """
    DRF API endpoint to send a test notification
    POST /api/notifications/send-test/
    """
    if not request.user.is_staff:
        return Response(
            {"error": "Staff permissions required"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    recipient_id = request.data.get('recipient_id')
    message = request.data.get('message', 'Test notification from admin')
    
    try:
        if recipient_id:
            recipient = get_object_or_404(User, id=recipient_id)
        else:
            recipient = request.user
        
        # Create test notification
        verb, _ = NotificationVerb.objects.get_or_create(name="test")
        
        notification = Notification.objects.create(
            recipient=recipient,
            verb=verb,
            description=message,
            target_content_type=None,
            target_object_id=None,
        )
        
        return Response({
            "success": True,
            "message": f"Test notification sent to {recipient.username}",
            "notification_id": notification.id
        })
        
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        return Response({
            "success": False,
            "error": f"Failed to send notification: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cleanup_notifications_api(request):
    """
    DRF API endpoint to cleanup old notifications
    DELETE /api/notifications/cleanup/
    """
    if not request.user.is_staff:
        return Response(
            {"error": "Staff permissions required"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    days_old = int(request.data.get('days_old', 30))
    read_only = request.data.get('read_only', True)
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        query = Q(created_at__lt=cutoff_date)
        if read_only:
            query &= Q(is_read=True)
        
        old_notifications = Notification.objects.filter(query)
        count = old_notifications.count()
        
        if not request.data.get('preview_only', False):
            old_notifications.delete()
        
        return Response({
            "success": True,
            "message": f"{'Would delete' if request.data.get('preview_only') else 'Deleted'} {count} notifications",
            "deleted_count": count,
            "criteria": f"{'Read' if read_only else 'All'} notifications older than {days_old} days"
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up notifications: {str(e)}")
        return Response({
            "success": False,
            "error": f"Failed to cleanup notifications: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# HTML Management UI Views
@login_required
@staff_or_perm('can_manage_notifications')
def notification_management_view(request):
    """
    HTML interface for notification management
    GET/POST /api/admin/notification-management/
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'send_test':
            recipient_id = request.POST.get('recipient_id')
            message = request.POST.get('message', 'Test notification from admin')
            
            try:
                if recipient_id:
                    recipient = get_object_or_404(User, id=int(recipient_id))
                else:
                    recipient = request.user
                
                verb, _ = NotificationVerb.objects.get_or_create(name="test")
                
                notification = Notification.objects.create(
                    recipient=recipient,
                    verb=verb,
                    description=message,
                    target_content_type=None,
                    target_object_id=None,
                )
                
                return JsonResponse({
                    "success": True,
                    "message": f"Test notification sent to {recipient.username}"
                })
                
            except Exception as e:
                logger.error(f"Error sending test notification: {str(e)}")
                return JsonResponse({
                    "success": False,
                    "error": f"Failed to send notification: {str(e)}"
                })
        
        elif action == 'cleanup':
            days_old = int(request.POST.get('days_old', 30))
            read_only = request.POST.get('read_only') == 'on'
            preview_only = request.POST.get('preview_only') == 'on'
            
            try:
                cutoff_date = timezone.now() - timedelta(days=days_old)
                
                query = Q(created_at__lt=cutoff_date)
                if read_only:
                    query &= Q(is_read=True)
                
                old_notifications = Notification.objects.filter(query)
                count = old_notifications.count()
                
                if not preview_only:
                    old_notifications.delete()
                
                return JsonResponse({
                    "success": True,
                    "message": f"{'Would delete' if preview_only else 'Deleted'} {count} notifications",
                    "deleted_count": count
                })
                
            except Exception as e:
                logger.error(f"Error cleaning up notifications: {str(e)}")
                return JsonResponse({
                    "success": False,
                    "error": f"Failed to cleanup notifications: {str(e)}"
                })
    
    # GET request - show management interface
    # Get stats for display
    total_notifications = Notification.objects.count()
    unread_notifications = Notification.objects.filter(is_read=False).count()
    recent_notifications = Notification.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Get notification verbs
    notification_verbs = NotificationVerb.objects.annotate(
        notification_count=Count('notification')
    ).order_by('-notification_count')
    
    # Get list of users for test notifications
    users = User.objects.filter(is_active=True).order_by('username')[:50]
    
    context = {
        "total_notifications": total_notifications,
        "unread_notifications": unread_notifications,
        "recent_notifications": recent_notifications,
        "notification_verbs": notification_verbs,
        "users": users,
        "page_title": "Notification Management"
    }
    
    return render(request, 'admin/notification_management.html', context)


@login_required
def user_notification_settings_view(request):
    """
    User interface for notification preferences
    GET/POST /api/notifications/settings/
    """
    # For now, this is a simple view - can be expanded for notification preferences
    user_notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:20]
    
    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    context = {
        "user_notifications": user_notifications,
        "unread_count": unread_count,
        "page_title": "My Notifications"
    }
    
    return render(request, 'portal/notification_settings.html', context)