# api/calendar_django_views.py
"""
Django views for calendar HTML pages
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse
from .models import Property, User
from .authz import AuthzHelper
import json

# DRF imports for API views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


class CalendarView(LoginRequiredMixin, View):
    """
    Main calendar view with HTML template
    """
    template_name = 'calendar/calendar_view.html'
    
    def get(self, request):
        """Render the calendar page"""
        context = {
            'user': request.user,
            'can_view_tasks': hasattr(request.user, 'profile') and request.user.profile.has_permission('view_all_tasks'),
            'can_view_bookings': True,  # Simplified - you might want to implement proper booking permissions
        }
        return render(request, self.template_name, context)


@require_http_methods(["GET"])
def calendar_properties_api(request):
    """
    API endpoint to get calendar data (bookings and tasks) for calendar display
    """
    from .models import Task, Booking
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Get date parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # If no date parameters, return just properties for filter options
    if not start_date or not end_date:
        properties = Property.objects.filter(is_deleted=False).values('id', 'name')
        return JsonResponse(list(properties), safe=False)
    
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Get filter parameters
    property_id = request.GET.get('property_id')
    status = request.GET.get('status')
    user_id = request.GET.get('user_id')
    
    # Build base queries
    tasks_query = Task.objects.filter(
        is_deleted=False,
        due_date__date__gte=start_dt,
        due_date__date__lte=end_dt
    )
    
    bookings_query = Booking.objects.filter(
        is_deleted=False
    ).filter(
        Q(check_in_date__date__lte=end_dt) & Q(check_out_date__date__gte=start_dt)
    )
    
    # Apply property filter
    if property_id:
        tasks_query = tasks_query.filter(property_ref_id=property_id)
        bookings_query = bookings_query.filter(property_id=property_id)
    
    # Apply status filter
    if status:
        tasks_query = tasks_query.filter(status=status)
        bookings_query = bookings_query.filter(status=status)
    
    # Apply user filter (for tasks only, as bookings don't have assigned users)
    if user_id:
        tasks_query = tasks_query.filter(assigned_to_id=user_id)
    
    # Execute queries
    tasks = tasks_query
    bookings = bookings_query
    
    # Enhanced color scheme for better visual distinction and status indication
    def get_task_color(status):
        """Get color based on task status with diverse, distinct colors"""
        color_map = {
            'pending': '#f39c12',      # Orange - needs attention
            'in-progress': '#3498db',  # Blue - actively being worked on
            'completed': '#27ae60',    # Green - done
            'cancelled': '#95a5a6',    # Gray - cancelled
            'overdue': '#e74c3c',      # Red - urgent/overdue
            'waiting_dependency': '#9b59b6',  # Purple - waiting for dependency
        }
        return color_map.get(status, '#3498db')  # Default blue for unknown status
    
    def get_booking_color(status):
        """Get color based on booking status with diverse, distinct colors"""
        color_map = {
            'pending': '#f39c12',           # Orange - pending confirmation
            'confirmed': '#27ae60',         # Green - confirmed
            'booked': '#16a085',           # Teal - booked
            'in-progress': '#3498db',       # Blue - currently hosting
            'currently_hosting': '#3498db', # Blue - currently hosting
            'owner_staying': '#8e44ad',     # Purple - owner staying
            'cancelled': '#95a5a6',         # Gray - cancelled
            'completed': '#27ae60',         # Green - completed
        }
        return color_map.get(status, '#27ae60')  # Default green for unknown status
    
    # Create events list
    events = []
    
    # Add tasks
    for task in tasks:
        events.append({
            'id': f"task_{task.id}",
            'title': task.title,
            'start': task.due_date.isoformat() if task.due_date else None,
            'end': task.due_date.isoformat() if task.due_date else None,
            'allDay': True,  # Tasks are all-day events
            'color': get_task_color(task.status),
            'type': 'task',
            'status': task.status,
            'property': task.property_ref.name if task.property_ref else '',
            'assigned_to': f"{task.assigned_to.first_name} {task.assigned_to.last_name}".strip() if task.assigned_to and (task.assigned_to.first_name or task.assigned_to.last_name) else (task.assigned_to.username if task.assigned_to else ''),
        })
    
    # Add bookings
    for booking in bookings:
        events.append({
            'id': f"booking_{booking.id}",
            'title': f"{booking.guest_name} - {booking.property.name}",
            'start': booking.check_in_date.isoformat() if booking.check_in_date else None,
            'end': booking.check_out_date.isoformat() if booking.check_out_date else None,
            'color': get_booking_color(booking.status),
            'type': 'booking',
            'status': booking.status,
            'property': booking.property.name,
            'guest_name': booking.guest_name,
        })
    
    return JsonResponse(events, safe=False)


@require_http_methods(["GET"])
def calendar_users_api(request):
    """
    API endpoint to get users for calendar filters
    """
    users = User.objects.filter(is_active=True).values('id', 'username', 'first_name', 'last_name')
    return JsonResponse(list(users), safe=False)


@require_http_methods(["GET"])
def calendar_stats_api(request):
    """
    API endpoint to get calendar statistics
    """
    from .models import Task, Booking
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    month_start = today.replace(day=1)
    
    # Get user's accessible tasks and bookings
    user = request.user
    
    # Tasks
    if user.is_superuser:
        tasks = Task.objects.filter(is_deleted=False)
        bookings = Booking.objects.filter(is_deleted=False)
    else:
        # Apply permission filtering
        tasks = Task.objects.filter(is_deleted=False)
        bookings = Booking.objects.filter(is_deleted=False)
        
        # Filter tasks based on user permissions
        if hasattr(user, 'profile'):
            if not (user.profile.has_permission('view_tasks') or user.profile.has_permission('view_all_tasks')):
                tasks = tasks.filter(Q(assigned_to=user) | Q(created_by=user))
    
    stats = {
        'total_tasks': tasks.count(),
        'pending_tasks': tasks.filter(status='pending').count(),
        'in_progress_tasks': tasks.filter(status='in-progress').count(),
        'completed_tasks': tasks.filter(status='completed').count(),
        'total_bookings': bookings.count(),
        'active_bookings': bookings.filter(
            check_in_date__date__lte=today,
            check_out_date__date__gte=today
        ).count(),
        'week_tasks': tasks.filter(due_date__date__range=[week_start, week_end]).count(),
        'month_tasks': tasks.filter(due_date__date__gte=month_start).count(),
    }
    
    return JsonResponse(stats)


@require_http_methods(["GET"])
def calendar_data_api(request):
    """
    API endpoint to get calendar data (bookings and tasks) without authentication
    """
    from .models import Task, Booking
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date or not end_date:
        return JsonResponse({'error': 'start_date and end_date parameters required'}, status=400)
    
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Get tasks in the date range
    tasks = Task.objects.filter(
        is_deleted=False,
        due_date__date__gte=start_dt,
        due_date__date__lte=end_dt
    )
    
    # Get bookings in the date range  
    bookings = Booking.objects.filter(
        is_deleted=False
    ).filter(
        Q(check_in_date__date__lte=end_dt) & Q(check_out_date__date__gte=start_dt)
    )
    
    # Create events list
    events = []
    
    # Enhanced color scheme for better visual distinction and status indication
    def get_task_color(status):
        """Get color based on task status with diverse, distinct colors"""
        color_map = {
            'pending': '#f39c12',      # Orange - needs attention
            'in-progress': '#3498db',  # Blue - actively being worked on
            'completed': '#27ae60',    # Green - done
            'cancelled': '#95a5a6',    # Gray - cancelled
            'overdue': '#e74c3c',      # Red - urgent/overdue
            'waiting_dependency': '#9b59b6',  # Purple - waiting for dependency
        }
        return color_map.get(status, '#3498db')  # Default blue for unknown status
    
    def get_booking_color(status):
        """Get color based on booking status with diverse, distinct colors"""
        color_map = {
            'pending': '#f39c12',           # Orange - pending confirmation
            'confirmed': '#27ae60',         # Green - confirmed
            'booked': '#16a085',           # Teal - booked
            'in-progress': '#3498db',       # Blue - currently hosting
            'currently_hosting': '#3498db', # Blue - currently hosting
            'owner_staying': '#8e44ad',     # Purple - owner staying
            'cancelled': '#95a5a6',         # Gray - cancelled
            'completed': '#27ae60',         # Green - completed
        }
        return color_map.get(status, '#27ae60')  # Default green for unknown status
    
    # Add tasks
    for task in tasks:
        events.append({
            'id': f"task_{task.id}",
            'title': task.title,
            'start': task.due_date.isoformat() if task.due_date else None,
            'end': task.due_date.isoformat() if task.due_date else None,
            'allDay': True,  # Tasks are all-day events
            'color': get_task_color(task.status),
            'type': 'task',
            'status': task.status,
            'property': task.property_ref.name if task.property_ref else '',
            'assigned_to': f"{task.assigned_to.first_name} {task.assigned_to.last_name}".strip() if task.assigned_to and (task.assigned_to.first_name or task.assigned_to.last_name) else (task.assigned_to.username if task.assigned_to else ''),
        })
    
    # Add bookings
    for booking in bookings:
        events.append({
            'id': f"booking_{booking.id}",
            'title': f"{booking.guest_name} - {booking.property.name}",
            'start': booking.check_in_date.isoformat() if booking.check_in_date else None,
            'end': booking.check_out_date.isoformat() if booking.check_out_date else None,
            'color': get_booking_color(booking.status),
            'type': 'booking',
            'status': booking.status,
            'property': booking.property.name,
            'guest_name': booking.guest_name,
        })
    
    return JsonResponse(events, safe=False)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendar_events_api(request):
    """
    API endpoint to get events for a date range (for calendar display)
    """
    from .models import Task, Booking
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Get include/exclude parameters
    include_tasks = request.GET.get('include_tasks', 'true').lower() == 'true'
    include_bookings = request.GET.get('include_bookings', 'true').lower() == 'true'
    
    # Get filter parameters
    property_id = request.GET.get('property_id')
    status_filter = request.GET.get('status')
    user_id = request.GET.get('user_id')
    event_type_filter = request.GET.get('event_type')
    
    # If no date parameters provided, use default range (current month)
    if not start_date or not end_date:
        today = timezone.now().date()
        start_dt = today.replace(day=1)  # First day of current month
        # Last day of current month
        if today.month == 12:
            end_dt = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_dt = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    else:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get tasks in the date range
    tasks = Task.objects.filter(
        is_deleted=False,
        due_date__date__gte=start_dt,
        due_date__date__lte=end_dt
    )
    
    # Get bookings in the date range
    bookings = Booking.objects.filter(
        is_deleted=False
    ).filter(
        Q(check_in_date__date__lte=end_dt) & Q(check_out_date__date__gte=start_dt)
    )
    
    # Apply property filter
    if property_id:
        tasks = tasks.filter(property_ref_id=property_id)
        bookings = bookings.filter(property_id=property_id)
    
    # Apply status filter
    if status_filter:
        tasks = tasks.filter(status=status_filter)
        bookings = bookings.filter(status=status_filter)
    
    # Apply user filter (for tasks only, as bookings don't have assigned users)
    if user_id:
        tasks = tasks.filter(assigned_to_id=user_id)
    
    # Apply event type filter
    if event_type_filter:
        if event_type_filter == 'task':
            include_bookings = False
        elif event_type_filter == 'booking':
            include_tasks = False
    
    # Manually serialize the data without DRF serializers
    events = []
    
    # Enhanced color scheme for better visual distinction and status indication
    def get_task_color(status):
        """Get color based on task status with diverse, distinct colors"""
        color_map = {
            'pending': '#f39c12',      # Orange - needs attention
            'in-progress': '#3498db',  # Blue - actively being worked on
            'completed': '#27ae60',    # Green - done
            'cancelled': '#95a5a6',    # Gray - cancelled
            'overdue': '#e74c3c',      # Red - urgent/overdue
            'waiting_dependency': '#9b59b6',  # Purple - waiting for dependency
        }
        return color_map.get(status, '#3498db')  # Default blue for unknown status
    
    def get_booking_color(status):
        """Get color based on booking status with diverse, distinct colors"""
        color_map = {
            'pending': '#f39c12',           # Orange - pending confirmation
            'confirmed': '#27ae60',         # Green - confirmed
            'booked': '#16a085',           # Teal - booked
            'in-progress': '#3498db',       # Blue - currently hosting
            'currently_hosting': '#3498db', # Blue - currently hosting
            'owner_staying': '#8e44ad',     # Purple - owner staying
            'cancelled': '#95a5a6',         # Gray - cancelled
            'completed': '#27ae60',         # Green - completed
        }
        return color_map.get(status, '#27ae60')  # Default green for unknown status
    
    # Add tasks to events (if included)
    if include_tasks:
        for task in tasks:
            events.append({
                'id': f"task_{task.id}",
                'title': task.title,
                'start': task.due_date.isoformat() if task.due_date else None,
                'end': task.due_date.isoformat() if task.due_date else None,
                'allDay': True,  # Tasks are all-day events
                'color': get_task_color(task.status),
                'type': 'task',
                'status': task.status,
                'property': task.property_ref.name if task.property_ref else '',
                'assigned_to': f"{task.assigned_to.first_name} {task.assigned_to.last_name}".strip() if task.assigned_to and (task.assigned_to.first_name or task.assigned_to.last_name) else (task.assigned_to.username if task.assigned_to else ''),
                'url': reverse('portal-task-detail', args=[task.id]),
            })
    
    # Add bookings to events (if included)
    if include_bookings:
        for booking in bookings:
            events.append({
                'id': f"booking_{booking.id}",
                'title': f"{booking.guest_name} - {booking.property.name}",
                'start': booking.check_in_date.isoformat() if booking.check_in_date else None,
                'end': booking.check_out_date.isoformat() if booking.check_out_date else None,
                'color': get_booking_color(booking.status),
                'type': 'booking',
                'status': booking.status,
                'property': booking.property.name,
                'guest_name': booking.guest_name,
                'url': reverse('portal-booking-detail', args=[booking.property.id, booking.id]),
            })
    
    return Response(events, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendar_day_events_api(request):
    """
    API endpoint to get events for a specific day
    """
    from .models import Task, Booking
    from django.utils import timezone
    from datetime import datetime, timedelta
    from .calendar_serializers import CalendarTaskSerializer, CalendarBookingSerializer
    
    date_str = request.GET.get('date')
    if not date_str:
        return Response({'error': 'Date parameter required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get tasks for the day
    tasks = Task.objects.filter(
        due_date__date=target_date,
        is_deleted=False
    )
    
    # Get bookings for the day
    bookings = Booking.objects.filter(
        Q(check_in_date__date=target_date) | 
        Q(check_out_date__date=target_date) |
        (Q(check_in_date__date__lte=target_date) & Q(check_out_date__date__gte=target_date)),
        is_deleted=False
    )
    
    # Serialize the data
    task_data = CalendarTaskSerializer(tasks, many=True).data
    booking_data = CalendarBookingSerializer(bookings, many=True).data
    
    # Convert to calendar events format
    events = []
    
    for task in task_data:
        events.append({
            'id': f"task_{task['id']}",
            'title': task['title'],
            'start': task['due_date'],
            'allDay': True,
            'type': 'task',
            'status': task['status'],
            'color': '#007bff',
            'property_name': task['property_name'],
            'assigned_to': task['assigned_to'],
            'description': task['description'],
            'url': reverse('portal-task-detail', args=[task['id']])
        })
    
    for booking in booking_data:
        # Get the property_id from the original booking object
        booking_obj = next((b for b in bookings if b.id == booking['id']), None)
        property_id = booking_obj.property.id if booking_obj else None
        
        events.append({
            'id': f"booking_{booking['id']}",
            'title': f"{booking['property_name']} - {booking['guest_name']}",
            'start': booking['check_in_date'],
            'end': booking['check_out_date'],
            'allDay': True,
            'type': 'booking',
            'status': booking['status'],
            'color': '#28a745',
            'property_name': booking['property_name'],
            'guest_name': booking['guest_name'],
            'description': f"Booking from {booking['check_in_date']} to {booking['check_out_date']}",
            'url': reverse('portal-booking-detail', args=[property_id, booking['id']]) if property_id else None
        })
    
    return Response({
        'date': date_str,
        'tasks': task_data,
        'bookings': booking_data,
        'events': events,
        'total_events': len(events)
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendar_tasks_api(request):
    """
    API endpoint to get tasks for calendar
    """
    from .models import Task
    from .calendar_serializers import CalendarTaskSerializer
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Get date range from query parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    tasks = Task.objects.filter(is_deleted=False)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            tasks = tasks.filter(due_date__date__gte=start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            tasks = tasks.filter(due_date__date__lte=end_dt)
        except ValueError:
            pass
    
    # Apply additional filters
    property_id = request.GET.get('property_id')
    if property_id:
        tasks = tasks.filter(property_ref_id=property_id)
    
    task_status = request.GET.get('status')
    if task_status:
        tasks = tasks.filter(status=task_status)
    
    user_id = request.GET.get('user_id')
    if user_id:
        tasks = tasks.filter(assigned_to_id=user_id)
    
    serializer = CalendarTaskSerializer(tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendar_bookings_api(request):
    """
    API endpoint to get bookings for calendar
    """
    from .models import Booking
    from .calendar_serializers import CalendarBookingSerializer
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Get date range from query parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    bookings = Booking.objects.filter(is_deleted=False)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            bookings = bookings.filter(check_in_date__date__gte=start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            bookings = bookings.filter(check_out_date__date__lte=end_dt)
        except ValueError:
            pass
    
    # Apply additional filters
    property_id = request.GET.get('property_id')
    if property_id:
        bookings = bookings.filter(property_id=property_id)
    
    booking_status = request.GET.get('status')
    if booking_status:
        bookings = bookings.filter(status=booking_status)
    
    serializer = CalendarBookingSerializer(bookings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@require_http_methods(["GET"])
def calendar_test_api(request):
    """
    Simple test API to check if Django views work without authentication
    """
    return JsonResponse({'status': 'success', 'message': 'Test API working'})
