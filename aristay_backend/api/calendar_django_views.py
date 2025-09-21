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
    API endpoint to get properties for calendar filters
    """
    # Check if this is a request for calendar data
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    print(f"DEBUG: start_date={start_date}, end_date={end_date}")
    
    if start_date and end_date:
        # Return calendar data instead of just properties
        from .models import Task, Booking
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
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
        
        # Add tasks
        for task in tasks:
            events.append({
                'id': f"task_{task.id}",
                'title': task.title,
                'start': task.due_date.isoformat() if task.due_date else None,
                'end': task.due_date.isoformat() if task.due_date else None,
                'color': '#007bff',
                'type': 'task',
                'status': task.status,
                'property': task.property_ref.name if task.property_ref else '',
                'assigned_to': f"{task.assigned_to.first_name} {task.assigned_to.last_name}" if task.assigned_to else '',
            })
        
        # Add bookings
        for booking in bookings:
            events.append({
                'id': f"booking_{booking.id}",
                'title': f"{booking.guest_name} - {booking.property.name}",
                'start': booking.check_in_date.isoformat() if booking.check_in_date else None,
                'end': booking.check_out_date.isoformat() if booking.check_out_date else None,
                'color': '#28a745',
                'type': 'booking',
                'status': booking.status,
                'property': booking.property.name,
                'guest_name': booking.guest_name,
            })
        
        return JsonResponse(events, safe=False)
    else:
        # Return properties as before
        properties = Property.objects.filter(is_deleted=False).values('id', 'name')
        return JsonResponse(list(properties), safe=False)


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
    
    # Add tasks
    for task in tasks:
        events.append({
            'id': f"task_{task.id}",
            'title': task.title,
            'start': task.due_date.isoformat() if task.due_date else None,
            'end': task.due_date.isoformat() if task.due_date else None,
            'color': '#007bff',
            'type': 'task',
            'status': task.status,
            'property': task.property_ref.name if task.property_ref else '',
            'assigned_to': f"{task.assigned_to.first_name} {task.assigned_to.last_name}" if task.assigned_to else '',
        })
    
    # Add bookings
    for booking in bookings:
        events.append({
            'id': f"booking_{booking.id}",
            'title': f"{booking.guest_name} - {booking.property.name}",
            'start': booking.check_in_date.isoformat() if booking.check_in_date else None,
            'end': booking.check_out_date.isoformat() if booking.check_out_date else None,
            'color': '#28a745',
            'type': 'booking',
            'status': booking.status,
            'property': booking.property.name,
            'guest_name': booking.guest_name,
        })
    
    return JsonResponse(events, safe=False)


@require_http_methods(["GET"])
def calendar_events_api(request):
    """
    API endpoint to get events for a date range (for calendar display)
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
        is_deleted=False,
        Q(check_in_date__date__lte=end_dt) & Q(check_out_date__date__gte=start_dt)
    )
    
    # Manually serialize the data without DRF serializers
    events = []
    
    # Add tasks to events
    for task in tasks:
        events.append({
            'id': f"task_{task.id}",
            'title': task.title,
            'start': task.due_date.isoformat() if task.due_date else None,
            'end': task.due_date.isoformat() if task.due_date else None,
            'color': '#007bff',
            'type': 'task',
            'status': task.status,
            'property': task.property_ref.name if task.property_ref else '',
            'assigned_to': f"{task.assigned_to.first_name} {task.assigned_to.last_name}" if task.assigned_to else '',
        })
    
    # Add bookings to events
    for booking in bookings:
        events.append({
            'id': f"booking_{booking.id}",
            'title': f"{booking.guest_name} - {booking.property.name}",
            'start': booking.check_in_date.isoformat() if booking.check_in_date else None,
            'end': booking.check_out_date.isoformat() if booking.check_out_date else None,
            'color': '#28a745',
            'type': 'booking',
            'status': booking.status,
            'property': booking.property.name,
            'guest_name': booking.guest_name,
        })
    
    return JsonResponse(events, safe=False)


@require_http_methods(["GET"])
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
        return JsonResponse({'error': 'Date parameter required'}, status=400)
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
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
            'assigned_to': task['assigned_to_username'],
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
    
    return JsonResponse({
        'date': date_str,
        'tasks': task_data,
        'bookings': booking_data,
        'events': events,
        'total_events': len(events)
    })


@require_http_methods(["GET"])
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
    
    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)
    
    user_id = request.GET.get('user_id')
    if user_id:
        tasks = tasks.filter(assigned_to_id=user_id)
    
    serializer = CalendarTaskSerializer(tasks, many=True)
    return JsonResponse(serializer.data, safe=False)


@require_http_methods(["GET"])
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
    
    status = request.GET.get('status')
    if status:
        bookings = bookings.filter(status=status)
    
    serializer = CalendarBookingSerializer(bookings, many=True)
    return JsonResponse(serializer.data, safe=False)
