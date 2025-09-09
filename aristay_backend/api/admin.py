from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Q, Count
from django.contrib.admin import DateFieldListFilter
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from datetime import datetime
import json
import logging
from .models import (
    Property, Task, TaskImage, Notification, Booking, PropertyOwnership, Profile,
    ChecklistTemplate, ChecklistItem, TaskChecklist, ChecklistResponse, ChecklistPhoto,
    InventoryCategory, InventoryItem, PropertyInventory, InventoryTransaction,
    LostFoundItem, LostFoundPhoto, ScheduleTemplate, GeneratedTask,
    BookingImportTemplate, BookingImportLog, CustomPermission, RolePermission, UserPermissionOverride,
    AuditEvent, AutoTaskTemplate  # Agent's Phase 2: Add audit system and task templates
)
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin


class ProvenanceStampMixin:
    """Mixin to stamp modified_by/modified_via consistently when available."""
    provenance_via = 'admin'

    def save_model(self, request, obj, form, change):
        # If the model has these fields, set them
        if hasattr(obj, 'modified_by'):
            obj.modified_by = request.user
        if hasattr(obj, 'modified_via'):
            obj.modified_via = self.provenance_via
        super().save_model(request, obj, form, change)

def create_unified_history_view(model_class):
    """
    Create a unified history view function for any model that has a history field.
    This combines Django admin history with the model's custom history field.
    """
    def history_view(self, request, object_id, extra_context=None):
        """Custom history view that combines Django admin history with model.history field"""
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 CUSTOM HISTORY VIEW CALLED for {model_class.__name__} {object_id}")
        
        # Get the object
        obj = self.get_object(request, object_id)
        if obj is None:
            raise Http404(f"{model_class.__name__} not found")
        
        logger.info(f"📋 {model_class.__name__} found: {getattr(obj, 'name', getattr(obj, 'title', str(obj)))}")
        
        # Get Django admin history
        content_type = ContentType.objects.get_for_model(obj)
        django_history = LogEntry.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).order_by('-action_time')
        
        # Get model.history field
        model_history = []
        try:
            history_field = getattr(obj, 'history', None)
            if history_field:
                model_history = json.loads(history_field or '[]')
        except json.JSONDecodeError:
            model_history = []
        
        logger.info(f"📝 {model_class.__name__}.history field: {len(model_history)} entries")
        
        # Combine and sort histories by timestamp
        combined_history = []
        
        # Add Django admin history
        for entry in django_history:
            # Ensure timezone-aware datetime
            timestamp = entry.action_time
            if timestamp.tzinfo is None:
                from django.utils import timezone
                timestamp = timezone.make_aware(timestamp)
            
            combined_history.append({
                'timestamp': timestamp,
                'user': entry.user.username if entry.user else 'System',
                'action': entry.get_action_flag_display(),
                'changes': entry.change_message,
                'type': 'admin'
            })
        
        # Add model.history entries
        for entry in model_history:
            if isinstance(entry, str) and ': ' in entry:
                try:
                    # Parse format: "2025-01-08T10:30:00.000000+00:00: username changed ..."
                    # Important: split on ": " to avoid splitting inside ISO time
                    timestamp_str, _, change_desc = entry.partition(': ')
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Ensure timezone-aware datetime
                    if timestamp.tzinfo is None:
                        from django.utils import timezone
                        timestamp = timezone.make_aware(timestamp)
                    
                    # Extract user from "<user> changed ..."
                    user_name = 'Unknown'
                    if change_desc:
                        parts = change_desc.split(' changed ', 1)
                        if parts and parts[0]:
                            user_name = parts[0].strip()
                    combined_history.append({
                        'timestamp': timestamp,
                        'user': user_name,
                        'action': 'Changed',
                        'changes': change_desc.strip(),
                        'type': 'dashboard'
                    })
                except (ValueError, IndexError):
                    # Skip malformed entries
                    continue
        
        # Sort by timestamp (newest first)
        combined_history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Create context
        context = {
            'title': f'History for {getattr(obj, "name", getattr(obj, "title", str(obj)))}',
            'object': obj,
            'history': combined_history,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request, obj),
        }
        
        if extra_context:
            context.update(extra_context)
        
        return render(request, 'admin/task_history.html', context)
    
    return history_view


class ConflictStatusFilter(admin.SimpleListFilter):
    """Custom filter for booking conflicts"""
    title = _('Conflict Status')
    parameter_name = 'conflict_status'

    def lookups(self, request, model_admin):
        return [
            ('no_conflicts', _('No Conflicts')),
            ('has_conflicts', _('Has Conflicts')),
            ('critical', _('Critical Conflicts')),
            ('high', _('High Priority')),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'no_conflicts':
            # Bookings with no conflicts - this is tricky to filter efficiently
            # For now, we'll show all and let the display method handle it
            return queryset
        elif self.value() == 'has_conflicts':
            # This would require complex filtering, for now return all
            return queryset
        elif self.value() == 'critical':
            # Filter bookings that might have critical conflicts
            return queryset.filter(
                Q(status__in=['booked', 'confirmed', 'currently_hosting'])
            )
        elif self.value() == 'high':
            return queryset.filter(
                Q(status__in=['booked', 'confirmed', 'currently_hosting'])
            )
        return queryset


class DateRangeFilter(admin.SimpleListFilter):
    """Custom filter for date ranges"""
    title = _('Date Range')
    parameter_name = 'date_range'

    def lookups(self, request, model_admin):
        return [
            ('today', _('Today')),
            ('this_week', _('This Week')),
            ('this_month', _('This Month')),
            ('next_week', _('Next Week')),
            ('next_month', _('Next Month')),
        ]

    def queryset(self, request, queryset):
        from datetime import datetime, timedelta
        from django.utils import timezone

        now = timezone.now()
        today = now.date()

        if self.value() == 'today':
            return queryset.filter(
                Q(check_in_date__date=today) | Q(check_out_date__date=today)
            )
        elif self.value() == 'this_week':
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            return queryset.filter(
                Q(check_in_date__date__range=[week_start, week_end]) |
                Q(check_out_date__date__range=[week_start, week_end])
            )
        elif self.value() == 'this_month':
            month_start = today.replace(day=1)
            next_month = month_start.replace(month=month_start.month % 12 + 1, day=1)
            month_end = next_month - timedelta(days=1)
            return queryset.filter(
                Q(check_in_date__date__range=[month_start, month_end]) |
                Q(check_out_date__date__range=[month_start, month_end])
            )
        elif self.value() == 'next_week':
            next_week_start = today + timedelta(days=7 - today.weekday())
            next_week_end = next_week_start + timedelta(days=6)
            return queryset.filter(
                Q(check_in_date__date__range=[next_week_start, next_week_end]) |
                Q(check_out_date__date__range=[next_week_start, next_week_end])
            )
        elif self.value() == 'next_month':
            if today.month == 12:
                next_month_start = today.replace(year=today.year + 1, month=1, day=1)
            else:
                next_month_start = today.replace(month=today.month + 1, day=1)
            # Calculate the first day of the month after next_month_start
            if next_month_start.month == 12:
                first_day_after = next_month_start.replace(year=next_month_start.year + 1, month=1, day=1)
            else:
                first_day_after = next_month_start.replace(month=next_month_start.month + 1, day=1)
            next_month_end = first_day_after - timedelta(days=1)
            return queryset.filter(
                Q(check_in_date__date__range=[next_month_start, next_month_end]) |
                Q(check_out_date__date__range=[next_month_start, next_month_end])
            )
        return queryset


class CustomAdminSite(admin.AdminSite):
    site_header = "AriStay Administration"
    site_title = "AriStay Admin"
    index_title = "Welcome to AriStay Administration"
    
    def has_permission(self, request):
        # Restrict Superuser admin to Superusers only
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)
    
    def login(self, request, extra_context=None):
        """
        Custom login that provides better error messages for non-superusers
        """
        from django.contrib.auth import authenticate, login
        from django.contrib import messages
        from django.shortcuts import redirect
        
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            if username and password:
                user = authenticate(request, username=username, password=password)
                if user and user.is_authenticated:
                    if not user.is_superuser:
                        # Check if user is a manager - redirect to manager admin
                        try:
                            if hasattr(user, 'profile') and user.profile and user.profile.role == 'manager':
                                login(request, user)  # Log them in first
                                return redirect('/manager/')  # Redirect to manager admin
                        except:
                            pass
                            
                        messages.error(request, 
                            'Access Denied: You don\'t have permission to access the admin site. '
                            'Only superuser accounts can access this area.')
                        # Don't proceed with login for non-superusers
                        return super().login(request, extra_context)
        
        return super().login(request, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('analytics/', self.admin_view(self.analytics_view), name='admin_analytics'),
        ]
        return custom_urls + urls
    
    def analytics_view(self, request):
        # Redirect to our charts dashboard
        return HttpResponseRedirect('/api/admin/charts/')

# Use the custom admin site
admin_site = CustomAdminSite(name='admin')

class TaskImageInline(admin.TabularInline):
    model = TaskImage
    extra = 0
    readonly_fields = ('uploaded_at', 'preview')
    fields = ('image', 'preview', 'uploaded_at')

    def preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="100" height="100" style="object-fit: cover;" />'
        return "No image"
    preview.allow_tags = True
    preview.short_description = 'Image Preview'

class TaskAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('id', 'title', 'task_type', 'status', 'property_ref', 'booking', 'assigned_to', 'created_at_display', 'due_date_display')
    list_filter = ('status', 'task_type', 'created_at', 'property_ref', 'booking', 'assigned_to')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'modified_at', 'history', 'created_at_dual', 'modified_at_dual', 'due_date_dual')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'task_type', 'property_ref', 'booking', 'status', 'assigned_to', 'due_date', 'depends_on')
        }),
        ('Tracking', {
            'fields': ('created_by', 'created_at_dual', 'modified_by', 'modified_at_dual', 'due_date_dual'),
            'classes': ('collapse',)
        }),
        ('History', {
            'fields': ('history',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TaskImageInline]
    
    # Use the generic unified history view
    history_view = create_unified_history_view(Task)

    def created_at_display(self, obj):
        """Display created time in Tampa timezone"""
        from django.utils import timezone
        import pytz
        if obj.created_at:
            tampa_tz = pytz.timezone('America/New_York')
            tampa_time = obj.created_at.astimezone(tampa_tz)
            return tampa_time.strftime('%b %d, %Y %H:%M (Tampa, FL)')
        return '-'
    created_at_display.short_description = 'Created (Tampa, FL)'
    
    def due_date_display(self, obj):
        """Display due date in Tampa timezone"""
        from django.utils import timezone
        import pytz
        if obj.due_date:
            tampa_tz = pytz.timezone('America/New_York')
            tampa_time = obj.due_date.astimezone(tampa_tz)
            return tampa_time.strftime('%b %d, %Y %H:%M (Tampa, FL)')
        return '-'
    due_date_display.short_description = 'Due Date (Tampa, FL)'
    
    def created_at_dual(self, obj):
        """Display created time in dual timezones for detail view"""
        from django.utils import timezone
        import pytz
        if obj.created_at:
            # Get user timezone from request if available
            user_tz = self._get_user_timezone()
            tampa_tz = pytz.timezone('America/New_York')
            
            user_time = obj.created_at.astimezone(user_tz)
            tampa_time = obj.created_at.astimezone(tampa_tz)
            
            if str(user_tz) == str(tampa_tz):
                return tampa_time.strftime('%b %d, %Y %H:%M (Tampa, FL)')
            else:
                user_tz_name = self._get_timezone_name(str(user_tz))
                return f"{user_time.strftime('%b %d, %Y %H:%M')} ({user_tz_name}) | {tampa_time.strftime('%b %d, %Y %H:%M')} (Tampa, FL)"
        return '-'
    created_at_dual.short_description = 'Created'
    
    def modified_at_dual(self, obj):
        """Display modified time in dual timezones for detail view"""
        from django.utils import timezone
        import pytz
        if obj.modified_at:
            user_tz = self._get_user_timezone()
            tampa_tz = pytz.timezone('America/New_York')
            
            user_time = obj.modified_at.astimezone(user_tz)
            tampa_time = obj.modified_at.astimezone(tampa_tz)
            
            if str(user_tz) == str(tampa_tz):
                return tampa_time.strftime('%b %d, %Y %H:%M (Tampa, FL)')
            else:
                user_tz_name = self._get_timezone_name(str(user_tz))
                return f"{user_time.strftime('%b %d, %Y %H:%M')} ({user_tz_name}) | {tampa_time.strftime('%b %d, %Y %H:%M')} (Tampa, FL)"
        return '-'
    modified_at_dual.short_description = 'Modified'
    
    def due_date_dual(self, obj):
        """Display due date in dual timezones for detail view"""
        from django.utils import timezone
        import pytz
        if obj.due_date:
            user_tz = self._get_user_timezone()
            tampa_tz = pytz.timezone('America/New_York')
            
            user_time = obj.due_date.astimezone(user_tz)
            tampa_time = obj.due_date.astimezone(tampa_tz)
            
            if str(user_tz) == str(tampa_tz):
                return tampa_time.strftime('%b %d, %Y %H:%M (Tampa, FL)')
            else:
                user_tz_name = self._get_timezone_name(str(user_tz))
                return f"{user_time.strftime('%b %d, %Y %H:%M')} ({user_tz_name}) | {tampa_time.strftime('%b %d, %Y %H:%M')} (Tampa, FL)"
        return '-'
    due_date_dual.short_description = 'Due Date'
    
    def _get_user_timezone(self):
        """Get user timezone from profile or default to Tampa"""
        import pytz
        try:
            # Try to get timezone from the current request user
            if hasattr(self, 'request') and self.request and hasattr(self.request, 'user'):
                user = self.request.user
                if hasattr(user, 'profile') and user.profile and user.profile.timezone:
                    return pytz.timezone(user.profile.timezone)
        except:
            pass
        return pytz.timezone('America/New_York')  # Default to Tampa
    
    def _get_timezone_name(self, tz_string):
        """Get friendly timezone name"""
        timezone_names = {
            'America/New_York': 'Tampa, FL',
            'America/Los_Angeles': 'San Jose, CA', 
            'America/Chicago': 'Chicago, IL',
            'America/Denver': 'Denver, CO',
            'America/Phoenix': 'Phoenix, AZ',
            'Asia/Ho_Chi_Minh': 'Ho Chi Minh, Vietnam',
            'Europe/London': 'London, UK',
            'UTC': 'UTC',
        }
        return timezone_names.get(tz_string, tz_string)
    
    def get_form(self, request, obj=None, **kwargs):
        """Store request for timezone access"""
        self.request = request
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)

class PropertyAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'created_at', 'created_by')
    search_fields = ('name', 'address')
    readonly_fields = ('created_at', 'modified_at', 'history')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'address', 'created_by', 'modified_by')
        }),
        ('History', {
            'fields': ('history', 'created_at', 'modified_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Use the generic unified history view
    history_view = create_unified_history_view(Property)

    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)
        
class BookingAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = (
        'id', 'property', 'external_code_display', 'booked_on_display', 'source_display',
        'check_in_display', 'check_out_display', 'status', 'guest_name', 'guest_contact',
        'conflict_status_display', 'conflict_count_display'
    )
    list_filter = (
        'status', 'source', 'property',
        ('check_in_date', admin.DateFieldListFilter),
        ('check_out_date', admin.DateFieldListFilter),
        'same_day_flag', 'created_at', 'modified_at',
        ConflictStatusFilter,  # Custom filter for conflicts
        DateRangeFilter,  # Custom date range filter
    )
    search_fields = ('property__name', 'guest_name', 'guest_contact', 'external_code', 'source')
    readonly_fields = ('created_at', 'modified_at', 'history', 'check_in_dual', 'check_out_dual', 'created_at_dual', 'modified_at_dual')
    list_per_page = 25
    actions = ['resolve_conflicts', 'mark_as_reviewed']
    
    def resolve_conflicts(self, request, queryset):
        """Admin action to mark selected bookings as conflict-resolved"""
        updated = queryset.update(conflict_resolved=True)
        self.message_user(
            request,
            f'Successfully marked {updated} booking(s) as conflict resolved.',
            messages.SUCCESS
        )
    resolve_conflicts.short_description = "Mark selected bookings as conflict resolved"
    
    def mark_as_reviewed(self, request, queryset):
        """Admin action to mark selected bookings as reviewed"""
        updated = queryset.update(reviewed=True)
        self.message_user(
            request,
            f'Successfully marked {updated} booking(s) as reviewed.',
            messages.SUCCESS
        )
    mark_as_reviewed.short_description = "Mark selected bookings as reviewed"
    
    fieldsets = (
        (None, {
            'fields': ('property', 'guest_name', 'guest_contact', 'status', 'check_in_date', 'check_out_date')
        }),
        ('Excel Import Data', {
            'fields': ('external_code', 'external_status', 'source', 'listing_name', 'booked_on', 'adults', 'children', 'infants', 'nights'),
            'classes': ('collapse',)
        }),
        ('Timing & Notes', {
            'fields': ('check_in_time', 'check_out_time', 'same_day_note', 'same_day_flag'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('created_at_dual', 'modified_at_dual', 'raw_row', 'last_import_update'),
            'classes': ('collapse',)
        }),
        ('History', {
            'fields': ('history',),
            'classes': ('collapse',)
        }),
    )
    
    def external_code_display(self, obj):
        """Display external confirmation code"""
        if obj.external_code:
            return f"{obj.external_code}"
        return "-"
    external_code_display.short_description = 'Confirmation Code'
    external_code_display.admin_order_field = 'external_code'
    
    def booked_on_display(self, obj):
        """Display when the booking was made"""
        if obj.booked_on:
            from django.utils import timezone
            import pytz
            tampa_tz = pytz.timezone('America/New_York')
            tampa_time = obj.booked_on.astimezone(tampa_tz)
            return tampa_time.strftime('%b %d, %Y %H:%M')
        return "-"
    booked_on_display.short_description = 'Booked Date'
    booked_on_display.admin_order_field = 'booked_on'
    
    def source_display(self, obj):
        """Display booking source with formatting"""
        if obj.source:
            # Add color coding for different sources
            source_colors = {
                'airbnb': '#FF5A5F',
                'vrbo': '#0073E6', 
                'direct': '#28A745',
                'owner': '#6F42C1'
            }
            source_lower = obj.source.lower()
            color = source_colors.get(source_lower, '#6C757D')
            return mark_safe(f'<span style="color: {color}; font-weight: bold;">{obj.source}</span>')
        return "-"
    source_display.short_description = 'Booking Source'
    source_display.admin_order_field = 'source'
    
    def conflict_status_display(self, obj):
        """Display conflict status with clear visual indicators"""
        conflicts = obj.check_conflicts()
        if not conflicts:
            return mark_safe('<span style="color: #28a745; font-weight: bold;">✅ No Conflicts</span>')
        
        conflict_count = len(conflicts)
        critical_count = len([c for c in conflicts if c['severity'] == 'critical'])
        high_count = len([c for c in conflicts if c['severity'] == 'high'])
        
        if critical_count > 0:
            return mark_safe(f'<span style="color: #dc3545; font-weight: bold;" title="Critical conflicts require immediate attention">🚨 {critical_count} Critical</span>')
        elif high_count > 0:
            return mark_safe(f'<span style="color: #ffc107; font-weight: bold;" title="High priority conflicts need review">⚠️ {high_count} High Priority</span>')
        else:
            return mark_safe(f'<span style="color: #17a2b8; font-weight: bold;" title="Minor conflicts detected">ℹ️ {conflict_count} Minor</span>')
    conflict_status_display.short_description = 'Conflict Status'
    
    def conflict_count_display(self, obj):
        """Display conflict count with quick action button"""
        conflicts = obj.check_conflicts()
        if not conflicts:
            return mark_safe('<span style="color: #6c757d;">0</span>')
        
        conflict_count = len(conflicts)
        critical_count = len([c for c in conflicts if c['severity'] == 'critical'])
        
        # Create a button to view conflict details
        button_html = f'''
        <button type="button" 
                onclick="window.open('/admin/api/booking/{obj.id}/change/', '_blank')" 
                style="background: {'#dc3545' if critical_count > 0 else '#ffc107'}; 
                       color: white; 
                       border: none; 
                       padding: 2px 6px; 
                       border-radius: 3px; 
                       cursor: pointer; 
                       font-size: 11px;"
                title="Click to view booking details and resolve conflicts">
            {conflict_count}
        </button>
        '''
        return mark_safe(button_html)
    conflict_count_display.short_description = 'Conflicts'
    
    def check_in_display(self, obj):
        """Display check-in time in Tampa timezone"""
        from django.utils import timezone
        import pytz
        if obj.check_in_date:
            tampa_tz = pytz.timezone('America/New_York')
            tampa_time = obj.check_in_date.astimezone(tampa_tz)
            return tampa_time.strftime('%b %d, %Y %H:%M (Tampa, FL)')
        return '-'
    check_in_display.short_description = 'Check-in (Tampa, FL)'
    
    def check_out_display(self, obj):
        """Display check-out time in Tampa timezone"""
        from django.utils import timezone
        import pytz
        if obj.check_out_date:
            tampa_tz = pytz.timezone('America/New_York')
            tampa_time = obj.check_out_date.astimezone(tampa_tz)
            return tampa_time.strftime('%b %d, %Y %H:%M (Tampa, FL)')
        return '-'
    check_out_display.short_description = 'Check-out (Tampa, FL)'
    
    def check_in_dual(self, obj):
        """Display check-in time in dual timezones"""
        return self._format_dual_timezone(obj.check_in_date)
    check_in_dual.short_description = 'Check-in'
    
    def check_out_dual(self, obj):
        """Display check-out time in dual timezones"""
        return self._format_dual_timezone(obj.check_out_date)
    check_out_dual.short_description = 'Check-out'
    
    def created_at_dual(self, obj):
        """Display created time in dual timezones"""
        return self._format_dual_timezone(obj.created_at)
    created_at_dual.short_description = 'Created'
    
    def modified_at_dual(self, obj):
        """Display modified time in dual timezones"""
        return self._format_dual_timezone(obj.modified_at)
    modified_at_dual.short_description = 'Modified'
    
    def _format_dual_timezone(self, dt):
        """Helper method to format datetime in dual timezones"""
        from django.utils import timezone
        import pytz
        if dt:
            user_tz = self._get_user_timezone()
            tampa_tz = pytz.timezone('America/New_York')
            
            user_time = dt.astimezone(user_tz)
            tampa_time = dt.astimezone(tampa_tz)
            
            if str(user_tz) == str(tampa_tz):
                return tampa_time.strftime('%b %d, %Y %H:%M (Tampa, FL)')
            else:
                user_tz_name = self._get_timezone_name(str(user_tz))
                return f"{user_time.strftime('%b %d, %Y %H:%M')} ({user_tz_name}) | {tampa_time.strftime('%b %d, %Y %H:%M')} (Tampa, FL)"
        return '-'
    
    def _get_user_timezone(self):
        """Get user timezone from profile or default to Tampa"""
        import pytz
        try:
            if hasattr(self, 'request') and self.request and hasattr(self.request, 'user'):
                user = self.request.user
                if hasattr(user, 'profile') and user.profile and user.profile.timezone:
                    return pytz.timezone(user.profile.timezone)
        except:
            pass
        return pytz.timezone('America/New_York')
    
    def _get_timezone_name(self, tz_string):
        """Get friendly timezone name"""
        timezone_names = {
            'America/New_York': 'Tampa, FL',
            'America/Los_Angeles': 'San Jose, CA', 
            'America/Chicago': 'Chicago, IL',
            'America/Denver': 'Denver, CO',
            'America/Phoenix': 'Phoenix, AZ',
            'Asia/Ho_Chi_Minh': 'Ho Chi Minh, Vietnam',
            'Europe/London': 'London, UK',
            'UTC': 'UTC',
        }
        return timezone_names.get(tz_string, tz_string)
    
    def get_form(self, request, obj=None, **kwargs):
        """Store request for timezone access"""
        self.request = request
        return super().get_form(request, obj, **kwargs)
    
    # Use the generic unified history view
    history_view = create_unified_history_view(Booking)

class PropertyOwnershipAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('id', 'property', 'user', 'ownership_type', 'can_edit', 'created_at')
    list_filter = ('ownership_type', 'can_edit', 'property')
    search_fields = ('property__name', 'user__username', 'user__email')
    readonly_fields = ('created_at',)

class NotificationAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('id', 'recipient', 'task_title', 'verb', 'read', 'timestamp', 'read_at', 'push_sent')
    list_filter = ('read', 'verb', 'push_sent', 'timestamp')
    search_fields = ('recipient__username', 'task__title')
    readonly_fields = ('timestamp', 'push_sent')
    list_per_page = 50
    
    fieldsets = (
        (None, {
            'fields': ('recipient', 'task', 'verb', 'read', 'read_at')
        }),
        ('System Info', {
            'fields': ('timestamp', 'push_sent'),
            'classes': ('collapse',)
        }),
    )
    
    def task_title(self, obj):
        return obj.task.title if obj.task else 'N/A'
    task_title.short_description = 'Task Title'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'task')
    
    # Use the generic unified history view
    history_view = create_unified_history_view(Notification)

# Register models with the custom admin site
admin_site.register(Task, TaskAdmin)
admin_site.register(Property, PropertyAdmin)
admin_site.register(Notification, NotificationAdmin)
admin_site.register(Booking, BookingAdmin)
admin_site.register(PropertyOwnership, PropertyOwnershipAdmin)

# Also register with default admin for backward compatibility
admin.site.register(Task, TaskAdmin)
admin.site.register(Property, PropertyAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(PropertyOwnership, PropertyOwnershipAdmin)

# -------------------- User admin with Profile inline (Superuser admin and default admin) --------------------

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fk_name = 'user'
    fields = ('role', 'timezone', 'digest_opt_out')
    
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'role':
            kwargs['help_text'] = 'Select user role: Administration/Cleaning/Maintenance/Laundry/Lawn Pool'
        return super().formfield_for_choice_field(db_field, request, **kwargs)

class AriStayUserAdmin(ProvenanceStampMixin, DjangoUserAdmin):
    """
    Custom UserAdmin with role-based permissions:
    - Superusers: Full access (can modify passwords, usernames, groups)
    - Managers: Can modify groups, trigger password reset, but cannot modify usernames
    - Staff: Limited access
    """
    inlines = [ProfileInline]

    def get_inline_instances(self, request, obj=None):
        # Only show ProfileInline for existing users (not when adding)
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)

    list_display = ('username', 'email', 'is_active', 'is_staff', 'is_superuser', 'password_status', 'last_login', 'date_joined')

    # Override Django's default fieldsets to avoid field conflicts
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Password Status', {'fields': ('password_status_display',)}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'groups', 'user_permissions'),
            'classes': ('collapse',),
            'description': 'Note: User role (staff/manager) is set in the Profile section below. Django admin access (is_staff/is_superuser) will be automatically synced based on Profile role.'
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)}),
    )

    # Add fieldsets for creating new users (includes password fields)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'groups', 'user_permissions'),
            'classes': ('collapse',),
            'description': 'Note: User role (staff/manager) will be set via Profile after user creation. Django admin access will be automatically synced.'
        }),
    )

    def password_status(self, obj):
        """Display password status in the admin list view"""
        if obj.has_usable_password():
            return mark_safe('<span style="color: green;">✓ Has Password</span>')
        else:
            return mark_safe('<span style="color: red;">✗ No Password</span>')
    password_status.short_description = 'Password Status'
    password_status.admin_order_field = 'password'

    def has_permission(self, request):
        """Check if user has permission to access this admin interface"""
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly based on user permissions"""
        readonly_fields = []

        # If user is not superuser (i.e., is a manager), make username readonly
        if hasattr(request, 'user') and request.user and not request.user.is_superuser:
            readonly_fields.append('username')

        # Always make password status readonly (it's a computed field)
        if obj:  # Only for existing users
            readonly_fields.append('password_status_display')

        return readonly_fields

    def password_status_display(self, obj):
        """Display password status in the change form"""
        if obj.has_usable_password():
            return mark_safe('<strong style="color: green;">✓ User has a password set</strong>')
        else:
            return mark_safe('<strong style="color: red;">✗ No password set</strong>')
    password_status_display.short_description = 'Password Status'

    def get_form(self, request, obj=None, **kwargs):
        """Customize form fields based on user permissions"""
        form = super().get_form(request, obj, **kwargs)

        # For managers (not superusers), remove password change capability only when editing
        if not request.user.is_superuser:
            # Only remove password fields when EDITING existing users (obj exists)
            # For new users (obj is None), we need the password fields
            if obj is not None:  # This is an edit form, not an add form
                # Remove password fields for managers
                if 'password1' in form.fields:
                    del form.fields['password1']
                if 'password2' in form.fields:
                    del form.fields['password2']

        return form

    def save_model(self, request, obj, form, change):
        """Handle password changes and user creation with automatic Profile management"""
        # Handle password changes for superusers only
        if request.user.is_superuser:
            # Check if password fields were provided
            if form.cleaned_data.get('password1') and form.cleaned_data.get('password2'):
                obj.set_password(form.cleaned_data['password1'])

        # Save the user first - the post_save signal will handle Profile creation
        super().save_model(request, obj, form, change)
        
        # Log the creation if this is a new user
        if not change:  # This is a new user
            print(f"✅ Admin created new user '{obj.username}' - Profile will be created by signal")
            
    def save_formset(self, request, form, formset, change):
        """Override to handle Profile inline saves and sync is_staff/is_superuser"""
        super().save_formset(request, form, formset, change)
        
        # After saving Profile inline, ensure is_staff/is_superuser are synced correctly
        user = form.instance
        if hasattr(user, 'profile') and user.profile:
            from .models import UserRole
            # Set is_staff and is_superuser based on profile role
            should_have_staff_access = user.profile.role in [UserRole.MANAGER, UserRole.SUPERUSER]
            should_have_superuser_access = user.profile.role == UserRole.SUPERUSER
            
            changed = False
            if user.is_staff != should_have_staff_access:
                user.is_staff = should_have_staff_access
                changed = True
            if user.is_superuser != should_have_superuser_access:
                user.is_superuser = should_have_superuser_access
                changed = True
                
            if changed:
                user.save(update_fields=['is_staff', 'is_superuser'])
                print(f"✅ Admin synced is_staff={user.is_staff}, is_superuser={user.is_superuser} for {user.username} (role: {user.profile.role})")

    def get_actions(self, request):
        """Customize actions based on user permissions"""
        actions = super().get_actions(request)

        # Only superusers can bulk delete users
        if not request.user.is_superuser:
            if 'delete_selected' in actions:
                del actions['delete_selected']

        # Add password reset action for both superusers and managers
        actions['send_password_reset'] = (
            self.send_password_reset,
            'send_password_reset',
            'Send password reset email to selected users'
        )

        return actions

    def send_password_reset(self, request, queryset):
        """Send password reset emails to selected users"""
        from django.contrib.auth.forms import PasswordResetForm
        sent = 0
        failed = 0

        for user in queryset:
            if not user.email:
                failed += 1
                continue

            try:
                form = PasswordResetForm(data={'email': user.email})
                if form.is_valid():
                    form.save(
                        email_template_name="registration/password_reset_email.html",
                        request=request,
                    )
                    sent += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1

        if sent > 0:
            self.message_user(request, f"Password reset email sent to {sent} user(s).")
        if failed > 0:
            self.message_user(request, f"Failed to send password reset to {failed} user(s).", level='ERROR')

    send_password_reset.short_description = "Send password reset email"

    def get_urls(self):
        """Add custom URLs and override password change for managers"""
        from django.urls import path
        from django.contrib.admin.sites import AdminSite
        urls = super().get_urls()
        custom_urls = [
            path('<id>/password-reset/', AdminSite.admin_view(self, self.password_reset_view), name='user_password_reset'),
            # Override the default password change URL to restrict managers
            path('<id>/password/', AdminSite.admin_view(self, self.user_change_password), name='auth_user_password_change'),
        ]
        return custom_urls + urls

    def user_change_password(self, request, id, form_url=''):
        """Override password change to restrict managers"""
        from django.contrib import messages
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib.auth.forms import AdminPasswordChangeForm

        user = get_object_or_404(User, pk=id)

        # Only superusers can directly change passwords
        if not request.user.is_superuser:
            messages.error(request, "You don't have permission to change user passwords. Use the 'Send Password Reset Email' button instead.")
            return redirect('admin:api_user_change', id)

        # For superusers, use the normal Django password change form
        if request.method == 'POST':
            form = AdminPasswordChangeForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, f"Password changed successfully for {user.username}.")
                return redirect('admin:api_user_change', id)
        else:
            form = AdminPasswordChangeForm(user)

        context = {
            'form': form,
            'user': user,
            'title': f'Change password: {user.username}',
            'is_popup': False,
        }

        from django.shortcuts import render
        return render(request, 'admin/auth/user/change_password.html', context)

    def password_reset_view(self, request, id):
        """Custom password reset view for individual users"""
        from django.contrib.auth.forms import PasswordResetForm
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages

        user = get_object_or_404(User, pk=id)

        # Check permissions
        if not request.user.is_superuser and request.user != user:
            messages.error(request, "You don't have permission to reset this user's password.")
            return redirect('admin:auth_user_changelist')

        if not user.email:
            messages.error(request, f"User {user.username} doesn't have an email address.")
            return redirect('admin:auth_user_change', id)

        try:
            form = PasswordResetForm(data={'email': user.email})
            if form.is_valid():
                form.save(
                    email_template_name="registration/password_reset_email.html",
                    request=request,
                )
                messages.success(request, f"Password reset email sent to {user.username}.")
            else:
                messages.error(request, f"Failed to send password reset email to {user.username}.")
        except Exception as e:
            messages.error(request, f"Error sending password reset: {str(e)}")

        return redirect('admin:auth_user_change', id)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Customize the change view to add password reset button"""
        extra_context = extra_context or {}

        # Add password reset URL for both superusers and managers
        if object_id:
            from django.urls import reverse
            try:
                extra_context['password_reset_url'] = reverse('admin:user_password_reset', args=[object_id])
            except:
                pass

        return super().change_view(request, object_id, form_url, extra_context)

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete users"""
        if not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def changelist_view(self, request, extra_context=None):
        """Customize changelist view based on permissions"""
        # For managers, filter out superusers from the list
        if not request.user.is_superuser:
            self.list_filter = ('is_active', 'is_staff', 'groups', 'profile__role')
            # Override queryset to exclude superusers
            self.queryset = User.objects.exclude(is_superuser=True)

        return super().changelist_view(request, extra_context)

    def get_queryset(self, request):
        """Filter queryset based on user permissions"""
        qs = super().get_queryset(request)

        # Managers can only see non-superuser accounts
        if not request.user.is_superuser:
            qs = qs.exclude(is_superuser=True)

        return qs
    
    def history_view(self, request, object_id, extra_context=None):
        """Custom history view for User model (Django admin history + custom history)"""
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 CUSTOM HISTORY VIEW CALLED for User {object_id}")
        
        # Get the user object
        user = self.get_object(request, object_id)
        if user is None:
            raise Http404("User not found")
        
        logger.info(f"📋 User found: {user.username}")
        
        # Get Django admin history
        content_type = ContentType.objects.get_for_model(user)
        django_history = LogEntry.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).order_by('-action_time')
        
        # Get custom user history (if it exists)
        custom_history = []
        try:
            history_field = getattr(user, 'history', None)
            if history_field:
                custom_history = json.loads(history_field or '[]')
        except json.JSONDecodeError:
            custom_history = []
        
        # Get password reset history
        password_reset_history = []
        try:
            from api.password_reset_logs import get_user_password_reset_history
            password_reset_history = get_user_password_reset_history(user)
        except Exception as e:
            logger.error(f"Failed to get password reset history: {e}")
        
        # Combine custom history and password reset history
        all_custom_history = custom_history + password_reset_history
        
        logger.info(f"📝 User.history field: {len(custom_history)} entries")
        logger.info(f"📝 Password reset history: {len(password_reset_history)} entries")
        
        # Convert to combined history format
        combined_history = []
        
        # Add Django admin history
        for entry in django_history:
            # Ensure timezone-aware datetime
            timestamp = entry.action_time
            if timestamp.tzinfo is None:
                from django.utils import timezone
                timestamp = timezone.make_aware(timestamp)
            
            combined_history.append({
                'timestamp': timestamp,
                'user': entry.user.username if entry.user else 'System',
                'action': entry.get_action_flag_display(),
                'changes': entry.change_message,
                'type': 'admin'
            })
        
        # Add custom history (password resets, etc.)
        for entry in all_custom_history:
            if isinstance(entry, str) and ':' in entry:
                try:
                    timestamp_str, change_desc = entry.split(':', 1)
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    if timestamp.tzinfo is None:
                        from django.utils import timezone
                        timestamp = timezone.make_aware(timestamp)
                    
                    combined_history.append({
                        'timestamp': timestamp,
                        'user': change_desc.split(' ')[0] if change_desc else 'Unknown',
                        'action': 'Changed',
                        'changes': change_desc.strip(),
                        'type': 'dashboard'
                    })
                except (ValueError, IndexError):
                    continue
        
        # Sort by timestamp (newest first)
        combined_history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Create context
        context = {
            'title': f'History for {user.username}',
            'object': user,
            'history': combined_history,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request, user),
        }
        
        if extra_context:
            context.update(extra_context)
        
        return render(request, 'admin/task_history.html', context)


# Manager version of UserAdmin (more restricted)
class ManagerUserAdmin(AriStayUserAdmin):
    """
    Manager version of UserAdmin with additional restrictions
    """
    # Managers can see and edit groups/departments
    filter_horizontal = ('groups',)

    def get_fieldsets(self, request, obj=None):
        """Customize fieldsets for managers"""
        fieldsets = super().get_fieldsets(request, obj)

        # For managers, ensure they can see groups but not certain sensitive fields
        for name, field_options in fieldsets:
            if name == 'Permissions':
                # Managers can edit groups but not user permissions
                field_options['fields'] = ('groups',)

        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        """Customize form for managers"""
        form = super().get_form(request, obj, **kwargs)

        # Managers should not be able to modify is_staff or is_superuser
        if 'is_staff' in form.fields:
            form.fields['is_staff'].disabled = True
        if 'is_superuser' in form.fields:
            form.fields['is_superuser'].disabled = True

        return form


# Alias for backwards compatibility
SuperuserUserAdmin = AriStayUserAdmin

# Register on default admin site with profile inline
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, SuperuserUserAdmin)

# Register on custom admin site as well
try:
    admin_site.unregister(User)
except Exception:
    pass
admin_site.register(User, SuperuserUserAdmin)


# ============================================================================
# MVP Phase 1: Checklists, Inventory, Lost & Found Admin
# ============================================================================

# Checklist Admin
class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0
    fields = ('title', 'item_type', 'is_required', 'order', 'room_type')
    ordering = ['order', 'room_type']

class ChecklistTemplateAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'task_type', 'is_active', 'created_at', 'created_by')
    list_filter = ('task_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    inlines = [ChecklistItemInline]
    readonly_fields = ('created_at', 'history')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'task_type', 'description', 'is_active', 'created_by')
        }),
        ('History', {
            'fields': ('history', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    # Use the generic unified history view
    history_view = create_unified_history_view(ChecklistTemplate)

class ChecklistPhotoInline(admin.TabularInline):
    model = ChecklistPhoto
    extra = 0
    readonly_fields = ('uploaded_at', 'uploaded_by')

class ChecklistResponseAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('checklist', 'item', 'is_completed', 'completed_at', 'completed_by')
    list_filter = ('is_completed', 'completed_at', 'item__item_type')
    search_fields = ('checklist__task__title', 'item__title')
    readonly_fields = ('completed_at',)
    inlines = [ChecklistPhotoInline]

class TaskChecklistAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('task', 'template', 'completion_percentage', 'started_at', 'completed_at', 'completed_by')
    list_filter = ('template', 'started_at', 'completed_at')
    search_fields = ('task__title', 'template__name')
    readonly_fields = ('completion_percentage',)

# Inventory Admin
class InventoryItemInline(admin.TabularInline):
    model = InventoryItem
    extra = 0
    fields = ('name', 'unit', 'estimated_cost', 'is_active')

class InventoryCategoryAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('name', 'description', 'icon')
    search_fields = ('name', 'description')
    inlines = [InventoryItemInline]

class InventoryItemAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'unit', 'estimated_cost', 'is_active', 'created_at')
    list_filter = ('category', 'unit', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'brand', 'sku')
    readonly_fields = ('created_at', 'history')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'unit', 'description', 'brand', 'sku', 'estimated_cost', 'is_active')
        }),
        ('History', {
            'fields': ('history', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Use the generic unified history view
    history_view = create_unified_history_view(InventoryItem)

class InventoryTransactionInline(admin.TabularInline):
    model = InventoryTransaction
    extra = 0
    readonly_fields = ('created_at', 'created_by')
    fields = ('transaction_type', 'quantity', 'task', 'notes', 'reference')

class PropertyInventoryAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('id', 'property_ref', 'item', 'current_stock', 'par_level', 'max_level', 'stock_status', 'last_updated')
    list_filter = ('item__category', 'last_updated')
    search_fields = ('property_ref__name', 'item__name')
    readonly_fields = ('stock_status', 'last_updated', 'history')
    inlines = [InventoryTransactionInline]
    
    fieldsets = (
        (None, {
            'fields': ('property_ref', 'item', 'current_stock', 'par_level', 'max_level', 'storage_location', 'updated_by')
        }),
        ('History', {
            'fields': ('history', 'last_updated'),
            'classes': ('collapse',)
        }),
    )
    
    def stock_status(self, obj):
        status = obj.stock_status
        colors = {
            'out_of_stock': 'red',
            'low_stock': 'orange', 
            'normal': 'green',
            'overstocked': 'blue'
        }
        from django.utils.html import format_html
        return format_html(
            '<span style="color: {}">{}</span>',
            colors.get(status, "black"),
            status.replace("_", " ").title()
        )
    stock_status.short_description = 'Stock Status'
    
    # Use the generic unified history view
    history_view = create_unified_history_view(PropertyInventory)

class InventoryTransactionAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('property_inventory', 'transaction_type', 'quantity', 'task', 'created_at', 'created_by')
    list_filter = ('transaction_type', 'created_at', 'property_inventory__property_ref')
    search_fields = ('property_inventory__property_ref__name', 'property_inventory__item__name', 'notes')
    readonly_fields = ('created_at',)
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    # Use the generic unified history view
    history_view = create_unified_history_view(InventoryTransaction)

# Lost & Found Admin
class LostFoundPhotoInline(admin.TabularInline):
    model = LostFoundPhoto
    extra = 0
    readonly_fields = ('uploaded_at', 'uploaded_by')

class LostFoundItemAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('title', 'property_ref', 'status', 'found_date', 'found_by', 'estimated_value')
    list_filter = ('status', 'found_date', 'property_ref', 'category')
    search_fields = ('title', 'description', 'property_ref__name', 'found_location')
    readonly_fields = ('found_date', 'history')
    inlines = [LostFoundPhotoInline]
    
    # Use the generic unified history view
    history_view = create_unified_history_view(LostFoundItem)
    
    def get_readonly_fields(self, request, obj=None):
        """Make history field read-only in the admin form"""
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if 'history' not in readonly_fields:
            readonly_fields.append('history')
        return readonly_fields

    def save_model(self, request, obj, form, change):
        # Stamp provenance so model.save can attribute correctly
        obj.modified_by = request.user
        obj.modified_via = 'admin'
        super().save_model(request, obj, form, change)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'category', 'estimated_value', 'property_ref', 'task', 'booking')
        }),
        ('Location & Status', {
            'fields': ('found_location', 'status', 'storage_location')
        }),
        ('Found Info', {
            'fields': ('found_date', 'found_by'),
            'classes': ('collapse',)
        }),
        ('Claimed Info', {
            'fields': ('claimed_date', 'claimed_by'),
            'classes': ('collapse',)
        }),
        ('Disposal Info', {
            'fields': ('disposal_date', 'disposal_method'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('History', {
            'fields': ('history',),
            'classes': ('collapse',)
        }),
    )

# Recurring Schedules Admin
class GeneratedTaskInline(admin.TabularInline):
    model = GeneratedTask
    extra = 0
    readonly_fields = ('task', 'generated_at', 'generated_for_date')
    can_delete = False

class ScheduleTemplateAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('name', 'task_type', 'property_ref', 'frequency', 'is_active', 'last_generated', 'created_at')
    list_filter = ('task_type', 'frequency', 'is_active', 'property_ref')
    search_fields = ('name', 'task_title_template', 'property_ref__name')
    readonly_fields = ('created_at', 'last_generated')
    inlines = [GeneratedTaskInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'task_type', 'property_ref', 'is_active')
        }),
        ('Task Template', {
            'fields': ('task_title_template', 'task_description_template', 'default_assignee', 'checklist_template')
        }),
        ('Schedule', {
            'fields': ('frequency', 'interval', 'weekday', 'day_of_month', 'start_date', 'end_date')
        }),
        ('Timing', {
            'fields': ('time_of_day', 'advance_days')
        }),
        ('System Info', {
            'fields': ('created_at', 'last_generated'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

class GeneratedTaskAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('id', 'schedule', 'task', 'generated_for_date', 'generated_at')
    list_filter = ('generated_for_date', 'generated_at', 'schedule__task_type')
    search_fields = ('schedule__name', 'task__title')
    readonly_fields = ('generated_at', 'history')
    
    fieldsets = (
        (None, {
            'fields': ('schedule', 'task', 'generated_for_date')
        }),
        ('History', {
            'fields': ('history', 'generated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Use the generic unified history view
    history_view = create_unified_history_view(GeneratedTask)

# Booking Import Admin
class BookingImportLogInline(admin.TabularInline):
    model = BookingImportLog
    extra = 0
    readonly_fields = ('imported_at', 'imported_by', 'total_rows', 'successful_imports', 'errors_count')
    can_delete = False

class BookingImportTemplateAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('name', 'property_ref', 'import_type', 'is_active', 'last_import', 'created_at')
    list_filter = ('import_type', 'is_active', 'property_ref')
    search_fields = ('name', 'property_ref__name')
    readonly_fields = ('created_at', 'last_import')
    inlines = [BookingImportLogInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'property_ref', 'import_type', 'is_active')
        }),
        ('CSV Field Mapping', {
            'fields': ('date_format', 'checkin_field', 'checkout_field', 'guest_name_field', 'guest_contact_field'),
            'classes': ('collapse',)
        }),
        ('Auto-Task Generation', {
            'fields': ('auto_create_tasks', 'cleaning_schedule')
        }),
        ('System Info', {
            'fields': ('created_at', 'last_import'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

class BookingImportLogAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('template', 'imported_at', 'imported_by', 'total_rows', 'successful_imports', 'errors_count')
    list_filter = ('imported_at', 'template')
    search_fields = ('template__name',)
    readonly_fields = ('imported_at',)


# ========== PERMISSION MANAGEMENT ADMIN ==========

@admin.action(description='Activate selected permissions')
def activate_permissions(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.action(description='Deactivate selected permissions')
def deactivate_permissions(modeladmin, request, queryset):
    queryset.update(is_active=False)

class CustomPermissionAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('name', 'get_display_name', 'is_active', 'created_at')
    list_filter = ('is_active', 'name')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    actions = [activate_permissions, deactivate_permissions]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('System Info', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_display_name(self, obj):
        """Get the human-readable name for the permission"""
        return dict(obj.PERMISSION_CHOICES).get(obj.name, obj.name)
    get_display_name.short_description = 'Display Name'
    get_display_name.admin_order_field = 'name'

class RolePermissionAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('role', 'permission', 'granted', 'can_delegate', 'created_by', 'created_at')
    list_filter = ('role', 'granted', 'can_delegate', 'permission__is_active')
    search_fields = ('permission__name', 'permission__description')
    readonly_fields = ('created_at',)
    autocomplete_fields = ['permission']
    
    fieldsets = (
        (None, {
            'fields': ('role', 'permission', 'granted', 'can_delegate')
        }),
        ('System Info', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('permission', 'created_by')

class UserPermissionOverrideAdmin(ProvenanceStampMixin, admin.ModelAdmin):
    list_display = ('user', 'permission', 'granted', 'granted_by', 'expires_at', 'is_expired_display', 'created_at')
    list_filter = ('granted', 'expires_at', 'created_at', 'permission__is_active')
    search_fields = ('user__username', 'user__email', 'permission__name', 'reason')
    readonly_fields = ('created_at', 'is_expired_display')
    autocomplete_fields = ['user', 'permission', 'granted_by']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'permission', 'granted', 'reason')
        }),
        ('Expiration', {
            'fields': ('expires_at',),
            'description': 'Leave blank for permanent override'
        }),
        ('System Info', {
            'fields': ('granted_by', 'created_at', 'is_expired_display'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)
    
    def is_expired_display(self, obj):
        """Display if the override has expired"""
        if obj.is_expired:
            return mark_safe('<span style="color: red; font-weight: bold;">✗ EXPIRED</span>')
        elif obj.expires_at:
            return mark_safe('<span style="color: orange;">⏰ WILL EXPIRE</span>')
        else:
            return mark_safe('<span style="color: green;">✓ PERMANENT</span>')
    is_expired_display.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'permission', 'granted_by')

# Add to ProfileAdmin to show permissions
class ProfileAdminWithPermissions(admin.ModelAdmin):
    list_display = ('user', 'role', 'timezone', 'departments_display', 'digest_opt_out')
    list_filter = ('role', 'timezone', 'digest_opt_out')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('user', 'permissions_summary')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'role', 'timezone')
        }),
        ('Contact Info', {
            'fields': ('phone_number', 'address'),
            'classes': ('collapse',)
        }),
        ('Notifications', {
            'fields': ('digest_opt_out',)
        }),
        ('Permissions Summary', {
            'fields': ('permissions_summary',),
            'description': 'Current permissions for this user (role + overrides)',
            'classes': ('collapse',)
        })
    )
    
    def permissions_summary(self, obj):
        """Display all permissions for this user"""
        if not obj:
            return "No profile"
        
        permissions = obj.get_all_permissions()
        if not permissions:
            return "No permissions assigned"
        
        granted = [name for name, granted in permissions.items() if granted]
        denied = [name for name, granted in permissions.items() if not granted]
        
        html = "<div style='font-family: monospace;'>"
        if granted:
            html += "<h4 style='color: green; margin: 5px 0;'>✓ GRANTED PERMISSIONS:</h4>"
            for perm in sorted(granted):
                display_name = dict(CustomPermission.PERMISSION_CHOICES).get(perm, perm)
                html += f"<div style='color: green; margin: 2px 0;'>✓ {display_name}</div>"
        
        if denied:
            html += "<h4 style='color: red; margin: 10px 0 5px 0;'>✗ DENIED PERMISSIONS:</h4>"
            for perm in sorted(denied):
                display_name = dict(CustomPermission.PERMISSION_CHOICES).get(perm, perm)
                html += f"<div style='color: red; margin: 2px 0;'>✗ {display_name}</div>"
        
        html += "</div>"
        return mark_safe(html)
    permissions_summary.short_description = 'User Permissions'


# Register all new models with custom admin site
admin_site.register(ChecklistTemplate, ChecklistTemplateAdmin)
admin_site.register(ChecklistResponse, ChecklistResponseAdmin)
admin_site.register(TaskChecklist, TaskChecklistAdmin)
admin_site.register(InventoryCategory, InventoryCategoryAdmin)
admin_site.register(InventoryItem, InventoryItemAdmin)
admin_site.register(PropertyInventory, PropertyInventoryAdmin)
admin_site.register(InventoryTransaction, InventoryTransactionAdmin)
admin_site.register(LostFoundItem, LostFoundItemAdmin)
admin_site.register(ScheduleTemplate, ScheduleTemplateAdmin)
admin_site.register(GeneratedTask, GeneratedTaskAdmin)
admin_site.register(BookingImportTemplate, BookingImportTemplateAdmin)
admin_site.register(BookingImportLog, BookingImportLogAdmin)

# Permission management
admin_site.register(CustomPermission, CustomPermissionAdmin)
admin_site.register(RolePermission, RolePermissionAdmin)
admin_site.register(UserPermissionOverride, UserPermissionOverrideAdmin)

# Also register with default admin for backward compatibility
admin.site.register(ChecklistTemplate, ChecklistTemplateAdmin)
admin.site.register(ChecklistResponse, ChecklistResponseAdmin)
admin.site.register(TaskChecklist, TaskChecklistAdmin)
admin.site.register(InventoryCategory, InventoryCategoryAdmin)
admin.site.register(InventoryItem, InventoryItemAdmin)
admin.site.register(PropertyInventory, PropertyInventoryAdmin)
admin.site.register(InventoryTransaction, InventoryTransactionAdmin)
admin.site.register(LostFoundItem, LostFoundItemAdmin)
admin.site.register(ScheduleTemplate, ScheduleTemplateAdmin)
admin.site.register(GeneratedTask, GeneratedTaskAdmin)
admin.site.register(BookingImportTemplate, BookingImportTemplateAdmin)
admin.site.register(BookingImportLog, BookingImportLogAdmin)

# Task Template System (registered via decorator in task_template_admin.py)
from . import task_template_admin  # Import to register admin

# Permission management (also register with default admin)
admin.site.register(CustomPermission, CustomPermissionAdmin)
admin.site.register(RolePermission, RolePermissionAdmin)


# =============================================================================
# AGENT'S PHASE 2: AUDIT SYSTEM ADMIN
# =============================================================================

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    """
    Agent's Phase 2: Admin interface for audit events with searchable fields and export.
    """
    list_display = [
        'created_at', 'action', 'object_type', 'object_id', 
        'actor', 'ip_address', 'request_id_short'
    ]
    list_filter = [
        'action',
        'object_type', 
        'created_at',
        ('actor', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'object_type',
        'object_id',
        'actor__username',
        'ip_address',
        'request_id',
    ]
    readonly_fields = [
        'object_type', 'object_id', 'action', 'actor', 
        'changes', 'request_id', 'ip_address', 'user_agent', 'created_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50
    
    def request_id_short(self, obj):
        """Display shortened request ID for better readability."""
        if obj.request_id:
            return obj.request_id[:8] + '...'
        return '-'
    request_id_short.short_description = 'Request ID'
    
    def has_add_permission(self, request):
        """Audit events are read-only."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Audit events are append-only, no deletion allowed."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Audit events are immutable."""
        return False
    
    def get_readonly_fields(self, request, obj=None):
        """All fields are readonly for audit events."""
        return [field.name for field in self.model._meta.fields]
    
    actions = ['export_audit_events']
    
    def export_audit_events(self, request, queryset):
        """Export selected audit events to CSV."""
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="audit_events_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Created At', 'Action', 'Object Type', 'Object ID', 
            'Actor', 'IP Address', 'Request ID', 'User Agent', 'Changes'
        ])
        
        for event in queryset:
            writer.writerow([
                event.created_at.isoformat(),
                event.action,
                event.object_type,
                event.object_id,
                event.actor.username if event.actor else 'System',
                event.ip_address or '',
                event.request_id,
                event.user_agent,
                str(event.changes)
            ])
        
        return response
    
    export_audit_events.short_description = "Export selected audit events to CSV"
admin.site.register(UserPermissionOverride, UserPermissionOverrideAdmin)