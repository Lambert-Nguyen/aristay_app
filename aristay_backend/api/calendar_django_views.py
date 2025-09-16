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


@login_required
@require_http_methods(["GET"])
def calendar_properties_api(request):
    """
    API endpoint to get properties for calendar filters
    """
    properties = Property.objects.filter(is_deleted=False).values('id', 'name')
    return JsonResponse(list(properties), safe=False)


@login_required
@require_http_methods(["GET"])
def calendar_users_api(request):
    """
    API endpoint to get users for calendar filters
    """
    users = User.objects.filter(is_active=True).values('id', 'username', 'first_name', 'last_name')
    return JsonResponse(list(users), safe=False)


@login_required
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
