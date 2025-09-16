# api/calendar_serializers.py
"""
Calendar-specific serializers for unified booking and task display
"""

from rest_framework import serializers
from .models import Task, Booking, Property
from django.utils import timezone
from datetime import datetime, date


class CalendarEventSerializer(serializers.Serializer):
    """
    Unified serializer for calendar events (both bookings and tasks)
    """
    id = serializers.IntegerField()
    title = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField(allow_null=True)
    allDay = serializers.BooleanField(default=False)
    type = serializers.CharField()  # 'booking' or 'task'
    status = serializers.CharField()
    color = serializers.CharField(allow_null=True)
    property_name = serializers.CharField(allow_null=True)
    guest_name = serializers.CharField(allow_null=True)
    assigned_to = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    url = serializers.CharField(allow_null=True)


class CalendarTaskSerializer(serializers.ModelSerializer):
    """Task serializer optimized for calendar display"""
    property_name = serializers.CharField(source='property_ref.name', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'status_display',
            'due_date', 'created_at', 'property_ref', 'property_name',
            'assigned_to', 'assigned_to_username', 'task_type'
        ]


class CalendarBookingSerializer(serializers.ModelSerializer):
    """Booking serializer optimized for calendar display"""
    property_name = serializers.CharField(source='property.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tasks_count = serializers.IntegerField(source='tasks.count', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'property', 'property_name', 'check_in_date', 'check_out_date',
            'guest_name', 'guest_contact', 'status', 'status_display',
            'external_code', 'tasks_count'
        ]


class CalendarFilterSerializer(serializers.Serializer):
    """Serializer for calendar filtering parameters"""
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    property_id = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)
    task_type = serializers.CharField(required=False)
    assigned_to = serializers.IntegerField(required=False)
    include_tasks = serializers.BooleanField(default=True)
    include_bookings = serializers.BooleanField(default=True)
