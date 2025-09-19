# api/calendar_views.py
"""
Calendar views for unified booking and task display
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, timedelta
from .models import Task, Booking, Property
from .calendar_serializers import (
    CalendarTaskSerializer,
    CalendarBookingSerializer,
    CalendarFilterSerializer,
)
from .permissions import DynamicTaskPermissions, DynamicBookingPermissions
from .authz import AuthzHelper


class CalendarViewSet(viewsets.ViewSet):
    """
    Calendar API endpoints for unified booking and task display
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset_tasks(self, user, filters=None):
        """Get tasks queryset based on user permissions and filters"""
        queryset = Task.objects.filter(is_deleted=False)
        
        # Apply user permission filtering
        if not user.is_superuser:
            profile = getattr(user, 'profile', None)
            if not (profile and (profile.has_permission('view_tasks') or profile.has_permission('view_all_tasks'))):
                # Fallback: show only tasks user is involved with
                queryset = queryset.filter(Q(assigned_to=user) | Q(created_by=user))
        
        # Apply filters
        if filters:
            if filters.get('property_id'):
                queryset = queryset.filter(property_ref_id=filters['property_id'])
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
            if filters.get('task_type'):
                queryset = queryset.filter(task_type=filters['task_type'])
            if filters.get('assigned_to'):
                queryset = queryset.filter(assigned_to_id=filters['assigned_to'])
            if filters.get('start_date'):
                queryset = queryset.filter(due_date__date__gte=filters['start_date'])
            if filters.get('end_date'):
                queryset = queryset.filter(due_date__date__lte=filters['end_date'])
        
        return queryset
    
    def get_queryset_bookings(self, user, filters=None):
        """Get bookings queryset based on user permissions and filters"""
        queryset = Booking.objects.filter(is_deleted=False)
        
        # Apply user permission filtering
        if not user.is_superuser:
            profile = getattr(user, 'profile', None)
            if not (profile and (profile.has_permission('view_bookings') or profile.has_permission('view_all_bookings'))):
                # Fallback: show bookings for properties user has access to
                # This is a simplified approach - you might want to implement more granular property access
                pass
        
        # Apply filters
        if filters:
            if filters.get('property_id'):
                queryset = queryset.filter(property_id=filters['property_id'])
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
            if filters.get('start_date'):
                queryset = queryset.filter(check_in_date__date__gte=filters['start_date'])
            if filters.get('end_date'):
                queryset = queryset.filter(check_out_date__date__lte=filters['end_date'])
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def events(self, request):
        """
        Get unified calendar events (bookings and tasks) for a date range
        """
        # Parse and validate filter parameters
        filter_serializer = CalendarFilterSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        filters = filter_serializer.validated_data
        
        # Set default date range if not provided
        if not filters.get('start_date'):
            filters['start_date'] = timezone.now().date() - timedelta(days=30)
        if not filters.get('end_date'):
            filters['end_date'] = timezone.now().date() + timedelta(days=30)
        
        events = []
        
        # Get tasks if requested
        if filters.get('include_tasks', True):
            tasks = self.get_queryset_tasks(request.user, filters)
            for task in tasks:
                if task.due_date:
                    # Determine color based on status
                    color_map = {
                        'pending': '#ffc107',  # amber
                        'waiting_dependency': '#6c757d',  # gray
                        'in-progress': '#007bff',  # blue
                        'completed': '#28a745',  # green
                        'canceled': '#dc3545',  # red
                    }
                    
                    event = {
                        'id': f"task_{task.id}",
                        'title': task.title,
                        'start': task.due_date.isoformat(),
                        'end': None,
                        'allDay': True,
                        'type': 'task',
                        'status': task.status,
                        'color': color_map.get(task.status, '#6c757d'),
                        'property_name': task.property_ref.name if task.property_ref else None,
                        'assigned_to': task.assigned_to.username if task.assigned_to else None,
                        'description': task.description,
                        'url': reverse('portal-task-detail', args=[task.id])
                    }
                    events.append(event)
        
        # Get bookings if requested
        if filters.get('include_bookings', True):
            bookings = self.get_queryset_bookings(request.user, filters)
            for booking in bookings:
                # Determine color based on status
                color_map = {
                    'booked': '#17a2b8',  # info
                    'confirmed': '#007bff',  # primary
                    'currently_hosting': '#28a745',  # success
                    'owner_staying': '#6f42c1',  # purple
                    'cancelled': '#dc3545',  # danger
                    'completed': '#6c757d',  # secondary
                }
                
                event = {
                    'id': f"booking_{booking.id}",
                    'title': f"{booking.guest_name} - {booking.property.name}",
                    'start': booking.check_in_date.isoformat(),
                    'end': booking.check_out_date.isoformat(),
                    'allDay': False,
                    'type': 'booking',
                    'status': booking.status,
                    'color': color_map.get(booking.status, '#6c757d'),
                    'property_name': booking.property.name,
                    'guest_name': booking.guest_name,
                    'assigned_to': None,
                    'description': f"Check-in: {booking.check_in_date.strftime('%Y-%m-%d %H:%M')}\nCheck-out: {booking.check_out_date.strftime('%Y-%m-%d %H:%M')}",
                    'url': reverse('portal-booking-detail', args=[booking.property.id, booking.id])
                }
                events.append(event)
        
        return Response(events)
    
    @action(detail=False, methods=['get'])
    def tasks(self, request):
        """
        Get tasks for calendar display
        """
        filter_serializer = CalendarFilterSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        filters = filter_serializer.validated_data
        tasks = self.get_queryset_tasks(request.user, filters)
        serializer = CalendarTaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def bookings(self, request):
        """
        Get bookings for calendar display
        """
        filter_serializer = CalendarFilterSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        filters = filter_serializer.validated_data
        bookings = self.get_queryset_bookings(request.user, filters)
        serializer = CalendarBookingSerializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def day_events(self, request):
        """
        Get all events for a specific day
        """
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'error': 'Date parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get tasks for the day
        tasks = self.get_queryset_tasks(request.user).filter(due_date__date=target_date)
        task_serializer = CalendarTaskSerializer(tasks, many=True)
        
        # Get bookings for the day (check-in or check-out on this date)
        bookings = self.get_queryset_bookings(request.user).filter(
            Q(check_in_date__date=target_date) | Q(check_out_date__date=target_date)
        )
        booking_serializer = CalendarBookingSerializer(bookings, many=True)
        
        return Response({
            'date': target_date.isoformat(),
            'tasks': task_serializer.data,
            'bookings': booking_serializer.data,
            'total_events': len(tasks) + len(bookings)
        })
