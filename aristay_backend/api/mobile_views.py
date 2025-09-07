# api/mobile_views.py
"""
Mobile-optimized endpoints for Flutter app
Compact, cacheable responses optimized for mobile bandwidth
"""
import logging
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter

from .models import Task, Property, Booking
from .authz import AuthzHelper

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Mobile"],
    operation_id="mobile_dashboard_data",
    summary="Get mobile dashboard data",
    description="Returns compact dashboard data optimized for mobile apps including task counts, properties, and activity.",
    responses={200: dict},
    examples=[OpenApiExample("Dashboard sample", value={
        "success": True, 
        "assigned_counts": {"total": 5, "pending": 2, "in_progress": 3, "overdue": 1},
        "properties": [{"id": 1, "name": "Property A", "address": "123 Main St"}],
        "recent_activity": 3,
        "server_time": "2025-09-07T12:00:00Z",
        "user_info": {"username": "staff", "role": "staff"}
    })],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mobile_dashboard_data(request):
    """
    Compact dashboard data optimized for mobile apps
    GET /api/mobile/dashboard/
    
    Returns minimal data needed for mobile dashboard:
    - Task counts for current user
    - Basic property list (limited to 50 most relevant)
    - Server time for synchronization
    """
    user = request.user
    
    try:
        # Get task counts efficiently
        user_tasks = Task.objects.filter(assigned_to=user)
        now = timezone.now()
        
        # Count tasks by status
        total_tasks = user_tasks.count()
        pending_tasks = user_tasks.filter(status='pending').count()
        in_progress_tasks = user_tasks.filter(status='in-progress').count()
        
        # Count overdue tasks
        overdue_tasks = user_tasks.filter(
            due_date__isnull=False,
            due_date__lt=now,
            status__in=['pending', 'in-progress']
        ).count()
        
        # Get accessible properties (limited for mobile)
        accessible_properties = AuthzHelper.get_accessible_properties(user)[:50]
        properties_data = [
            {
                "id": getattr(p, 'id', p.pk),
                "name": getattr(p, 'name', ''),
                "address": getattr(p, 'address', '') or ''
            }
            for p in accessible_properties
        ]
        
        # Get recent activity count
        recent_bookings = Booking.objects.filter(
            property__in=accessible_properties,
            created_at__gte=now - timezone.timedelta(days=7)
        ).count()
        
        return Response({
            "success": True,
            "assigned_counts": {
                "total": total_tasks,
                "pending": pending_tasks,
                "in_progress": in_progress_tasks,
                "overdue": overdue_tasks,
            },
            "properties": properties_data,
            "recent_activity": recent_bookings,
            "server_time": now.isoformat(),
            "user_info": {
                "username": user.username,
                "role": getattr(getattr(user, 'profile', None), 'role', 'staff'),
            }
        })
        
    except Exception as e:
        logger.error(f"Mobile dashboard data error for user {user.username}: {str(e)}")
        return Response({
            "success": False,
            "error": "Failed to load dashboard data"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=["Mobile"],
    operation_id="mobile_offline_sync",
    summary="Handle offline synchronization",
    description="Process arrays of changes made while offline including task completions and status updates.",
    request={
        "type": "object",
        "properties": {
            "completed_task_ids": {"type": "array", "items": {"type": "integer"}},
            "task_status_updates": {"type": "array", "items": {"type": "object"}},
            "checklist_updates": {"type": "array", "items": {"type": "object"}}
        }
    },
    responses={200: dict},
    examples=[OpenApiExample("Sync response", value={
        "success": True,
        "applied": {"completed_tasks": 2, "status_updates": 1, "checklist_updates": 0},
        "errors": [],
        "sync_time": "2025-09-07T12:00:00Z"
    })],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_offline_sync(request):
    """
    Handle offline synchronization for mobile app
    POST /api/mobile/offline-sync/
    
    Accepts arrays of changes made while offline:
    {
        "completed_task_ids": [1, 2, 3],
        "task_status_updates": [
            {"id": 4, "status": "in-progress"},
            {"id": 5, "status": "completed"}
        ],
        "checklist_updates": [
            {"task_id": 1, "item_id": 2, "completed": true}
        ]
    }
    
    Returns compact deltas for what was applied successfully
    """
    user = request.user
    
    try:
        data = request.data
        results = {
            "success": True,
            "applied": {},
            "errors": [],
            "sync_time": timezone.now().isoformat()
        }
        
        # Process completed tasks
        completed_task_ids = data.get('completed_task_ids', [])
        if completed_task_ids:
            updated_tasks = Task.objects.filter(
                id__in=completed_task_ids,
                assigned_to=user
            ).update(
                status='completed',
                modified_by=user,
                modified_at=timezone.now()
            )
            results["applied"]["completed_tasks"] = updated_tasks
        
        # Process task status updates
        task_updates = data.get('task_status_updates', [])
        applied_updates = 0
        for update in task_updates:
            task_id = None
            try:
                task_id = update.get('id')
                new_status = update.get('status')
                
                if task_id and new_status:
                    updated = Task.objects.filter(
                        id=task_id,
                        assigned_to=user
                    ).update(
                        status=new_status,
                        modified_by=user,
                        modified_at=timezone.now()
                    )
                    if updated:
                        applied_updates += 1
                        
            except Exception as e:
                task_id_str = str(task_id) if task_id is not None else "unknown"
                results["errors"].append(f"Task update {task_id_str}: {str(e)}")
        
        results["applied"]["status_updates"] = applied_updates
        
        # Process checklist updates (simplified for mobile)
        checklist_updates = data.get('checklist_updates', [])
        applied_checklist = 0
        for update in checklist_updates:
            task_id = None
            try:
                task_id = update.get('task_id')
                completed = update.get('completed', False)
                
                # This is a simplified implementation
                # In production, you'd want to update specific checklist items
                if task_id:
                    task = Task.objects.filter(
                        id=task_id,
                        assigned_to=user
                    ).first()
                    
                    if task and completed:
                        # Mark task as in-progress if not already completed
                        if task.status == 'pending':
                            task.status = 'in-progress'
                            task.modified_by = user
                            task.modified_at = timezone.now()
                            task.save(update_fields=['status', 'modified_by', 'modified_at'])
                            applied_checklist += 1
                            
            except Exception as e:
                task_id_str = str(task_id) if task_id is not None else "unknown"
                results["errors"].append(f"Checklist update {task_id_str}: {str(e)}")
        
        results["applied"]["checklist_updates"] = applied_checklist
        
        return Response(results)
        
    except Exception as e:
        logger.error(f"Mobile offline sync error for user {user.username}: {str(e)}")
        return Response({
            "success": False,
            "error": "Sync failed. Please try again."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=["Mobile"], 
    operation_id="mobile_task_summary",
    summary="Get compact task summary",
    description="Returns essential task information optimized for mobile display with filtering support.",
    parameters=[
        OpenApiParameter(name="status", description="Filter by task status", required=False, type=str),
        OpenApiParameter(name="property_id", description="Filter by property ID", required=False, type=int),
        OpenApiParameter(name="limit", description="Max results (max 50)", required=False, type=int)
    ],
    responses={200: dict},
    examples=[OpenApiExample("Task summary", value={
        "success": True,
        "tasks": [{"id": 1, "title": "Clean room", "status": "pending", "due_date": "2025-09-08T10:00:00Z"}],
        "count": 1,
        "server_time": "2025-09-07T12:00:00Z"
    })],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mobile_task_summary(request):
    """
    Compact task summary for mobile notifications and quick views
    GET /api/mobile/tasks/summary/
    
    Returns essential task information optimized for mobile display
    """
    user = request.user
    
    try:
        # Get user's tasks with minimal data
        user_tasks = Task.objects.filter(assigned_to=user).select_related(
            'property', 'booking'
        )
        
        # Apply filters
        status_filter = request.GET.get('status')
        if status_filter:
            user_tasks = user_tasks.filter(status=status_filter)
        
        property_filter = request.GET.get('property_id')
        if property_filter:
            user_tasks = user_tasks.filter(property_id=property_filter)
        
        # Limit results for mobile
        limit = min(int(request.GET.get('limit', 20)), 50)
        user_tasks = user_tasks[:limit]
        
        tasks_data = []
        for task in user_tasks:
            due_date = getattr(task, 'due_date', None)
            property_obj = getattr(task, 'property', None)
            
            tasks_data.append({
                "id": getattr(task, 'id', task.pk),
                "title": getattr(task, 'title', ''),
                "status": getattr(task, 'status', 'pending'),
                "due_date": due_date.isoformat() if due_date else None,
                "property_name": property_obj.name if property_obj else None,
                "task_type": getattr(task, 'task_type', ''),
                "priority": getattr(task, 'priority', 'normal'),
            })
        
        return Response({
            "success": True,
            "tasks": tasks_data,
            "count": len(tasks_data),
            "server_time": timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Mobile task summary error for user {user.username}: {str(e)}")
        return Response({
            "success": False,
            "error": "Failed to load task summary"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
