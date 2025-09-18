from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.urls import reverse
from django.conf import settings
from .services.notification_service import NotificationService
from .models import (
    NotificationVerb, Booking, BookingImportTemplate, BookingImportLog,
    CustomPermission, RolePermission, UserPermissionOverride, UserRole,
    Task, Property, TaskImage, Device, Notification, PropertyOwnership
)
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# Import auth mixin for JWT support
from .auth_mixins import DefaultAuthMixin

import json
import logging
import os
import re
from datetime import timedelta

# Set up logging
logger = logging.getLogger(__name__)

from .decorators import staff_or_perm, perm_required, manager_required
from .utils.json_utils import extract_conflicts_json
from .authz import AuthzHelper, can_edit_task
from .filters import TaskFilter
from .system_metrics import get_system_metrics

from rest_framework import generics, permissions, viewsets, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
)

from .serializers import (
    ManagerUserSerializer,
    TaskSerializer,
    PropertySerializer,
    UserSerializer,
    UserRegistrationSerializer,
    TaskImageSerializer,
    AdminInviteSerializer,
    AdminPasswordResetSerializer,
    AdminUserCreateSerializer,
    DeviceSerializer,
    NotificationSerializer,
    AdminUserAdminSerializer,
    BookingSerializer,
    PropertyOwnershipSerializer,
)
from .permissions import (
    IsOwnerOrAssignedOrReadOnly, IsOwner, IsManagerOrOwner,
    DynamicBookingPermissions, DynamicTaskPermissions, DynamicUserPermissions,
    DynamicPropertyPermissions, CanViewReports, CanViewAnalytics, CanAccessAdminPanel,
    CanManageFiles, HasCustomPermission
)


class TaskViewSet(DefaultAuthMixin, viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [DynamicTaskPermissions, IsOwnerOrAssignedOrReadOnly]

    filter_backends = [filters.SearchFilter, DjangoFilterBackend, OrderingFilter]
    # free-text search on title/description
    search_fields   = ['title', 'description']
    # use our custom FilterSet
    filterset_class = TaskFilter

    # Allow clients to order by these model fields:
    ordering_fields = [
        'due_date',
        'created_at',
        'modified_at',
        'status',
        'title',
    ]
    ordering        = ['due_date']

    # Add pagination for better performance
    pagination_class = PageNumberPagination

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        if not (self.request.user and self.request.user.is_authenticated):
            return queryset.none()
        
        # Superusers see everything
        if self.request.user.is_superuser:
            return queryset
        
        # Check if user has view_tasks or view_all_tasks permission (see all tasks)
        profile = getattr(self.request.user, 'profile', None)
        if profile and (profile.has_permission('view_tasks') or profile.has_permission('view_all_tasks')):
            return queryset
        
        # Fallback: show tasks the user is involved with
        return queryset.filter(Q(assigned_to=self.request.user) | Q(created_by=self.request.user))

    def perform_create(self, serializer):
        task = serializer.save(created_by=self.request.user, modified_by=self.request.user)
        NotificationService.notify_on_create(task, actor=self.request.user)

    def perform_update(self, serializer):
        # capture old BEFORE saving
        old = Task.objects.get(pk=serializer.instance.pk)
        task = serializer.save(modified_by=self.request.user)
        NotificationService.notify_on_update(old, task, actor=self.request.user)
        
    @action(
        detail=False,
        methods=['get'],
        url_path='count-by-status',
        permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    )
    def count_by_status(self, request):
        qs = self.filter_queryset(self.get_queryset())
        total = qs.count()

        counts = (
            qs.values('status')
            .annotate(count=Count('id'))
            .order_by()  # avoid implicit GROUP BY ordering issues
        )

        by_status = {entry['status']: entry['count'] for entry in counts}

        now = timezone.now()
        overdue = qs.filter(
            due_date__isnull=False,
            due_date__lt=now
        ).exclude(status__in=['completed', 'canceled']).count()
    
        return Response({
            'total': total,
            'by_status': by_status,
            'overdue': overdue,
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mute(self, request, pk=None):
        """
        POST /api/tasks/<id>/mute/
        """
        task = self.get_object()
        task.muted_by.add(request.user)
        return Response({'muted': True})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def notify_manager(self, request, pk=None):
        """
        POST /api/tasks/<id>/notify_manager/
        Sends a high-priority notification to managers/owners about this task.
        """
        task = self.get_object()
        # Use centralized authorization to get managers
        managers = AuthzHelper.get_manager_users()
        created = 0
        for user in managers.distinct():
            if user == request.user:
                continue
            Notification.objects.create(
                recipient=user,
                task=task,
                verb=NotificationVerb.STATUS_CHANGED,
            )
            created += 1
        return Response({'notified': created})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unmute(self, request, pk=None):
        task = self.get_object()
        task.muted_by.remove(request.user)
        return Response({'muted': False})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def assign_to_me(self, request, pk=None):
        task = self.get_object()
        old = Task.objects.get(pk=task.pk)
        task.assigned_to = request.user
        task.modified_by = request.user
        task.save(update_fields=['assigned_to', 'modified_by', 'modified_at'])
        NotificationService.notify_on_update(old, task, actor=request.user)
        return Response({'assigned_to': request.user.username})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def set_status(self, request, pk=None):
        task = self.get_object()
        new_status = request.data.get('status')
        valid = {s for s, _ in Task.STATUS_CHOICES}
        if new_status not in valid:
            return Response({'error': 'Invalid status'}, status=400)
        old = Task.objects.get(pk=task.pk)
        task.status = new_status
        task.modified_by = request.user
        task.save(update_fields=['status', 'modified_by', 'modified_at'])
        NotificationService.notify_on_update(old, task, actor=request.user)
        return Response({'status': new_status})


class BookingViewSet(DefaultAuthMixin, viewsets.ModelViewSet):
    queryset = Booking.objects.select_related('property').all()
    serializer_class = BookingSerializer
    permission_classes = [DynamicBookingPermissions]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ['guest_name', 'guest_contact', 'property_ref__name']
    ordering_fields = ['check_in_date', 'check_out_date', 'status']
    ordering = ['-check_in_date']

    # Add pagination for better performance
    pagination_class = PageNumberPagination

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        if not (self.request.user and self.request.user.is_authenticated):
            return queryset.none()
        
        # Superusers see everything
        if self.request.user.is_superuser:
            return queryset
        
        # Check if user has view_bookings permission
        if hasattr(self.request.user, 'profile') and self.request.user.profile:
            if self.request.user.profile.has_permission('view_bookings'):
                return queryset
        
        return queryset.none()


class PropertyOwnershipViewSet(DefaultAuthMixin, viewsets.ModelViewSet):
    queryset = PropertyOwnership.objects.select_related('property', 'user').all()
    serializer_class = PropertyOwnershipSerializer
    permission_classes = [DynamicPropertyPermissions]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['property__name', 'user__username', 'user__email']

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        if not (self.request.user and self.request.user.is_authenticated):
            return queryset.none()
        
        # Superusers see everything
        if self.request.user.is_superuser:
            return queryset
        
        # Check if user has view_properties permission
        if hasattr(self.request.user, 'profile') and self.request.user.profile:
            if self.request.user.profile.has_permission('view_properties'):
                return queryset
        
        return queryset.none()

# ----------------------------------------------------------------------------
# Portal (web) views – property → bookings → tasks flow
# ----------------------------------------------------------------------------

@login_required
def portal_home(request):
    
    # Get accessible properties and basic stats
    accessible_properties = _accessible_properties_for(request.user)
    accessible_properties_count = accessible_properties.count()
    
    # Get user-specific stats
    assigned_tasks_count = 0
    pending_tasks_count = 0
    total_bookings_count = 0
    
    try:
        if request.user.profile and request.user.profile.role != 'viewer':
            # Get task counts for non-viewers
            assigned_tasks = Task.objects.filter(assigned_to=request.user)
            assigned_tasks_count = assigned_tasks.count()
            pending_tasks_count = assigned_tasks.filter(status='pending').count()
    except AttributeError:
        # User has no profile, still get basic task counts
        assigned_tasks = Task.objects.filter(assigned_to=request.user)
        assigned_tasks_count = assigned_tasks.count()
        pending_tasks_count = assigned_tasks.filter(status='pending').count()
    
    # Get booking counts for accessible properties
    total_bookings_count = Booking.objects.filter(property__in=accessible_properties).count()
    
    context = {
        'user': request.user,
        'user_role': getattr(getattr(request.user, 'profile', None), 'role', 'staff'),
        'accessible_properties_count': accessible_properties_count,
        'assigned_tasks_count': assigned_tasks_count,
        'pending_tasks_count': pending_tasks_count,
        'total_bookings_count': total_bookings_count,
        'recent_activity_count': 0,  # Could be implemented later
    }
    return render(request, 'portal/home.html', context)


@login_required
def portal_calendar(request):
    """Portal calendar view with unified booking and task display"""
    context = {
        'user': request.user,
        'can_view_tasks': hasattr(request.user, 'profile') and request.user.profile.has_permission('view_all_tasks'),
        'can_view_bookings': True,  # Simplified - you might want to implement proper booking permissions
    }
    return render(request, 'portal/calendar.html', context)


def _accessible_properties_for(user):
    """Return a queryset of properties visible to this user."""
    if user.is_superuser:
        return Property.objects.all().order_by('name')
    
    # Check if user has manager role or wide property access permissions
    try:
        profile = user.profile
        if profile.role == UserRole.MANAGER or profile.has_permission('view_properties'):
            return Property.objects.all().order_by('name')
    except AttributeError:
        pass
    
    # viewer/owner or crew: properties they own/view or have tasks on
    owned = Property.objects.filter(ownerships__user=user)
    assigned = Property.objects.filter(tasks__assigned_to=user)
    return (owned | assigned).distinct().order_by('name')


@login_required
def portal_property_list(request):
    now = timezone.now()
    props = _accessible_properties_for(request.user)
    q = request.GET.get('q')
    if q:
        props = props.filter(name__icontains=q)
    # prefetch bookings for counts
    props = props.prefetch_related('bookings')
    property_cards = []
    for p in props:
        bookings = list(p.bookings.all())
        past = sum(1 for b in bookings if b.check_out_date and b.check_out_date <= now)
        current = sum(1 for b in bookings if b.check_in_date and b.check_out_date and b.check_in_date <= now < b.check_out_date)
        future = sum(1 for b in bookings if b.check_in_date and b.check_in_date > now)
        property_cards.append({
            'obj': p,
            'past_count': past,
            'current_count': current,
            'future_count': future,
        })
    return render(request, 'portal/property_list.html', {
        'properties': property_cards,
        'user': request.user,  # Add user to context
    })


@login_required
def portal_property_detail(request, pk):
    now = timezone.now()
    prop = get_object_or_404(_accessible_properties_for(request.user), pk=pk)
    bookings = prop.bookings.all().order_by('-check_in_date')
    groups = {
        'current': [],
        'future': [],
        'past': [],
    }
    for b in bookings:
        if b.check_in_date and b.check_out_date and b.check_in_date <= now < b.check_out_date:
            groups['current'].append(b)
        elif b.check_in_date and b.check_in_date > now:
            groups['future'].append(b)
        else:
            groups['past'].append(b)
    return render(request, 'portal/property_detail.html', {
        'property': prop,
        'groups': groups,
        'user': request.user,  # Add user to context
    })


@login_required
def portal_booking_detail(request, property_id, pk):
    prop = get_object_or_404(_accessible_properties_for(request.user), pk=property_id)
    booking = get_object_or_404(Booking.objects.filter(property=prop), pk=pk)
    tasks = Task.objects.filter(booking=booking).select_related('assigned_to')
    # Optional filters
    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)
    ttype = request.GET.get('type')
    if ttype:
        tasks = tasks.filter(task_type=ttype)
    q = request.GET.get('q')
    if q:
        tasks = tasks.filter(Q(title__icontains=q) | Q(description__icontains=q))
    # Pagination
    try:
        page = max(1, int(request.GET.get('page', '1')))
    except ValueError:
        page = 1
    page_size = 50
    start = (page - 1) * page_size
    end = start + page_size
    total = tasks.count()
    tasks = tasks.order_by('task_type', 'due_date', 'id')[start:end]
    # Group by task_type
    by_type = {
        'administration': [],
        'cleaning': [],
        'maintenance': [],
        'laundry': [],
        'lawn_pool': [],
    }
    for t in tasks:
        by_type.get(t.task_type, by_type.setdefault('administration', [])).append(t)

    return render(request, 'portal/booking_detail.html', {
        'property': prop,
        'booking': booking,
        'by_type': by_type,
        'all_statuses': [s for s, _ in Task.STATUS_CHOICES],
        'active_status': status or '',
        'active_type': ttype or '',
        'user': request.user,  # Add user to context
        'search_q': q or '',
        'page': page,
        'has_next': end < total,
        'has_prev': start > 0,
    })


@login_required
def portal_task_detail(request, task_id):
    """User-friendly task detail view for portal users."""
    
    task = get_object_or_404(Task.objects.select_related('property_ref', 'booking', 'assigned_to', 'created_by'), id=task_id)
    
    # Check permissions using centralized authorization
    if not AuthzHelper.can_view_task(request.user, task):
        raise DjangoPermissionDenied("You don't have permission to view this task.")
    
    # Get checklist if it exists
    checklist = None
    responses_by_room = {}
    try:
        checklist = task.checklist
        responses = checklist.responses.select_related('item').prefetch_related('photos')
        
        # Group responses by room type
        for response in responses:
            room = response.item.room_type or 'General'
            if room not in responses_by_room:
                responses_by_room[room] = []
            responses_by_room[room].append(response)
    except AttributeError:
        pass
    
    # Check if user can edit using centralized authorization
    can_edit = AuthzHelper.can_edit_task(request.user, task)
    
    context = {
        'task': task,
        'checklist': checklist,
        'responses_by_room': responses_by_room,
        'can_edit': can_edit,
        'user': request.user,  # Add user to context
    }
    
    return render(request, 'portal/task_detail.html', context)


# DRF ViewSets and API Views start here
# ============================================================================
        


class TaskImageCreateView(DefaultAuthMixin, generics.CreateAPIView):
    """
    POST /api/tasks/{task_pk}/images/
    Agent's enhanced upload: Accept large files, optimize server-side
    """
    serializer_class = TaskImageSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]  # object-level check in perform_create
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'evidence_upload'  # Agent's enhanced throttle scope

    def perform_create(self, serializer):
        # 1) load the Task and check permissions
        task = generics.get_object_or_404(Task, pk=self.kwargs['task_pk'])
        if not can_edit_task(self.request.user, task):
            raise DRFPermissionDenied("You can't add images to this task.")
        
        # 2) Auto-assign sequence number for the photo type
        photo_type = serializer.validated_data.get('photo_type', 'general')
        existing_photos = TaskImage.objects.filter(task=task, photo_type=photo_type)
        next_sequence = existing_photos.count() + 1
        
        # 3) save the new TaskImage with uploaded_by tracking and auto-assigned sequence
        image = serializer.save(
            task=task, 
            uploaded_by=self.request.user,
            sequence_number=next_sequence
        )
        
        # 4) update task history
        history = json.loads(task.history or '[]')
        history.append(f"{timezone.now().isoformat()}: {self.request.user.username} added photo {image.image.url}")
        Task.objects.filter(pk=task.pk).update(history=json.dumps(history))
        
        # 5) notify stakeholders
        NotificationService.notify_task_photo(task, added=True, actor=self.request.user)


class TaskImageListView(DefaultAuthMixin, generics.ListAPIView):
    """
    GET /api/tasks/{task_pk}/images/
    List all images for a specific task
    """
    serializer_class = TaskImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        task_pk = self.kwargs['task_pk']
        task = generics.get_object_or_404(Task, pk=task_pk)
        
        # Check if user has permission to view this task
        if not can_edit_task(self.request.user, task):
            raise DRFPermissionDenied("You can't view images for this task.")
        
        return TaskImage.objects.filter(task_id=task_pk).select_related('task', 'uploaded_by')

class TaskImageDetailView(DefaultAuthMixin, generics.RetrieveDestroyAPIView):
    """
    GET, DELETE /api/tasks/{task_pk}/images/{pk}/
    """
    serializer_class = TaskImageSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]  # object-level check in get_object

    def get_queryset(self):
        return TaskImage.objects.filter(task_id=self.kwargs['task_pk']).select_related('task')

    def get_object(self):
        obj = super().get_object()
        if not can_edit_task(self.request.user, obj.task):
            raise DRFPermissionDenied("You can't modify images on this task.")
        return obj

    def perform_destroy(self, instance):
        # 1) capture metadata before deletion
        task = instance.task
        url = instance.image.url
        # 2) delete the TaskImage record (and its file)
        instance.delete()
        # 3) append a "deleted photo" entry to task.history
        history = json.loads(task.history or '[]')
        history.append(f"{timezone.now().isoformat()}: {self.request.user.username} deleted photo {url}")
        Task.objects.filter(pk=task.pk).update(history=json.dumps(history))
        # notify
        NotificationService.notify_task_photo(task, added=False, actor=self.request.user)


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


# Legacy Task views - keeping for backward compatibility
class TaskListCreate(DefaultAuthMixin, generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [DynamicTaskPermissions]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TaskDetail(DefaultAuthMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [DynamicTaskPermissions, IsOwnerOrAssignedOrReadOnly]

    def perform_update(self, serializer):
        old = Task.objects.get(pk=serializer.instance.pk)
        instance = serializer.save(modified_by=self.request.user)

        changes = []
        for field in ('status', 'title', 'description', 'assigned_to', 'task_type'):
            old_val = getattr(old, field)
            new_val = getattr(instance, field)
            if field == 'assigned_to':
                old_val = old.assigned_to.username if old.assigned_to else None
                new_val = instance.assigned_to.username if instance.assigned_to else None

            if old_val != new_val:
                changes.append(
                    f"{timezone.now().isoformat()}: "
                    f"{self.request.user.username} changed {field} "
                    f"from '{old_val or ''}' to '{new_val or ''}'"
                )

        # Check property_ref changes separately  
        old_prop = old.property_ref.name if old.property_ref else None
        new_prop = instance.property_ref.name if instance.property_ref else None
        if old_prop != new_prop:
            changes.append(
                f"{timezone.now().isoformat()}: "
                f"{self.request.user.username} changed property "
                f"from '{old_prop or ''}' to '{new_prop or ''}'"
            )

        history = json.loads(old.history or '[]')
        history.extend(changes)
        Task.objects.filter(pk=instance.pk).update(history=json.dumps(history))


class PropertyListCreate(generics.ListCreateAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [DynamicPropertyPermissions]
    pagination_class = None

    def get_permissions(self):
        # only admins can create
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return super().get_permissions()
    
class PropertyDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [DynamicPropertyPermissions]

    def get_permissions(self):
        # Only admins can modify/delete; reads remain open to authenticated (or read-only if you prefer)
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdminUser()]
        return super().get_permissions()

class UserList(DefaultAuthMixin, generics.ListAPIView):
    queryset = User.objects.all().order_by('id')  # ← Add ordering to fix pagination warning
    serializer_class = UserSerializer
    permission_classes = [DynamicUserPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields  = ['username', 'email']

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        if not (self.request.user and self.request.user.is_authenticated):
            return queryset.none()
        
        # Superusers see everything
        if self.request.user.is_superuser:
            return queryset
        
        # Check if user has view_users permission
        if hasattr(self.request.user, 'profile') and self.request.user.profile:
            if self.request.user.profile.has_permission('view_users'):
                return queryset
        
        return queryset.none()

class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    """
    GET/PATCH /api/admin/users/<id>/
    Owner-only for updates. Safe fields: is_active.
    """
    queryset = User.objects.all()
    serializer_class = AdminUserAdminSerializer
    permission_classes = [DynamicUserPermissions]  # Now uses dynamic permissions

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        if not (self.request.user and self.request.user.is_authenticated):
            return queryset.none()
        
        # Superusers see everything
        if self.request.user.is_superuser:
            return queryset
        
        # Check if user has change_users permission for PATCH, view_users for GET
        if hasattr(self.request.user, 'profile') and self.request.user.profile:
            if self.request.method in ['PATCH', 'PUT']:
                if self.request.user.profile.has_permission('change_users'):
                    return queryset
            else:  # GET
                if self.request.user.profile.has_permission('view_users'):
                    return queryset
        
        return queryset.none()

    # (Optional safety: forbid changing superusers except by self)
    def perform_update(self, serializer):
        target: User = self.get_object()
        actor: User  = self.request.user
        data = serializer.validated_data

        # never allow anyone to toggle a superuser other than themselves
        if target.is_superuser and target != actor:
            raise DRFPermissionDenied("Cannot modify another owner account.")

        serializer.save()

class AdminInviteUserView(generics.CreateAPIView):
    """
    POST /api/admin/invite/
    { "username": "newuser", "email": "new@foo.com" }
    """
    serializer_class = AdminInviteSerializer
    permission_classes = [IsAdminUser]

class AdminPasswordResetView(generics.CreateAPIView):
    """
    POST /api/admin/reset-password/
    { "email": "existing@foo.com" }
    """
    serializer_class = AdminPasswordResetSerializer
    permission_classes = [IsAdminUser]

class CurrentUserView(DefaultAuthMixin, generics.RetrieveUpdateAPIView):
    """
    GET /api/users/me/
    """
    serializer_class       = UserSerializer
    permission_classes     = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    
class AdminUserCreateView(generics.CreateAPIView):
    """
    POST /api/admin/create-user/
    """
    permission_classes = [IsAdminUser]
    serializer_class   = AdminUserCreateSerializer

class DeviceRegisterView(generics.CreateAPIView):
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        token = request.data.get("token")

        if not token:
            return Response({"error": "No FCM token provided."}, status=400)

        # Step 1: remove any devices with this token (could be from another user)
        Device.objects.filter(token=token).delete()

        # Step 2: update existing device for user or create new one
        device, created = Device.objects.update_or_create(
            user=request.user,
            defaults={"token": token}
        )

        return Response({
            "status": "registered",
            "token": device.token,
            "created": created
        })

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['read']  # ← enables ?read=true / ?read=false

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        return (
            Notification.objects
            .filter(recipient=self.request.user)
            .order_by('-timestamp', '-id')  # newest first, stable
        )
        
@extend_schema(
    operation_id="unread_notification_count",
    summary="Get unread notification count",
    responses={200: inline_serializer(
        name="UnreadNotificationCountResponse",
        fields={
            "unread": serializers.IntegerField(),
        }
    )}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_notification_count(request):
    count = Notification.objects.filter(recipient=request.user, read=False).count()
    return Response({'unread': count})
    
@extend_schema(
    operation_id="mark_notification_read",
    summary="Mark a notification as read",
    request=None,
    responses=inline_serializer(
        name="MarkNotificationReadResponse",
        fields={
            "success": serializers.BooleanField(),
            "read_at": serializers.DateTimeField(),
        },
    ),
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):
    try:
        notif = Notification.objects.get(pk=pk, recipient=request.user)
    except Notification.DoesNotExist:
        return Response({'detail': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)

    notif.read = True
    notif.read_at = timezone.now()
    notif.save()

    return Response({'success': True, 'read_at': notif.read_at})

@extend_schema(
    operation_id="mark_all_notifications_read",
    summary="Mark all notifications as read for the current user",
    request=None,
    responses=inline_serializer(
        name="MarkAllNotificationsReadResponse",
        fields={
            "success": serializers.BooleanField(),
            "marked_count": serializers.IntegerField(help_text="Number of notifications marked as read"),
        },
    ),
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    count = Notification.objects.filter(recipient=request.user, read=False).update(
        read=True,
        read_at=timezone.now()
    )
    return Response({'success': True, 'marked_count': count})

# ---------- Manager dashboard: overview ----------
@extend_schema(
    operation_id="manager_overview_metrics",
    summary="Get overview metrics for manager dashboard",
    responses=inline_serializer(
        name="ManagerOverviewResponse",
        fields={
            "tasks": inline_serializer(
                name="TaskOverview",
                fields={
                    "total": serializers.IntegerField(),
                    "overdue": serializers.IntegerField(),
                    "by_status": serializers.DictField(),
                },
            ),
            "users": inline_serializer(
                name="UserOverview",
                fields={
                    "total": serializers.IntegerField(),
                    "active": serializers.IntegerField(),
                    "managers": serializers.IntegerField(),
                    "employees": serializers.IntegerField(),
                },
            ),
        },
    ),
)
@api_view(['GET'])
@permission_classes([CanViewAnalytics])
def manager_overview(request):
    qs = Task.objects.all()
    total = qs.count()
    now = timezone.now()
    overdue = (qs.filter(due_date__isnull=False, due_date__lt=now)
                 .exclude(status__in=['completed', 'canceled'])
                 .count())
    by = qs.values('status').annotate(count=Count('id')).order_by()
    by_status = {e['status']: e['count'] for e in by}

    users = User.objects.filter(is_superuser=False)
    managers  = users.filter(profile__role='manager').count()
    employees = users.filter(profile__role='staff').count()
    active    = users.filter(is_active=True).count()

    return Response({
        'tasks': {
            'total': total,
            'overdue': overdue,
            'by_status': by_status,
        },
        'users': {
            'total': users.count(),
            'active': active,
            'managers': managers,
            'employees': employees,
        }
    })

# ---------- Manager dashboard alias (compatibility) ----------
@extend_schema(
    operation_id="manager_dashboard",
    summary="Get overview metrics for manager dashboard (compatibility alias)",
    responses=inline_serializer(
        name="ManagerDashboardResponse",
        fields={
            "tasks": inline_serializer(
                name="DashboardTaskOverview",
                fields={
                    "total": serializers.IntegerField(),
                    "overdue": serializers.IntegerField(),
                    "by_status": serializers.DictField(),
                },
            ),
            "users": inline_serializer(
                name="DashboardUserOverview",
                fields={
                    "total": serializers.IntegerField(),
                    "active": serializers.IntegerField(),
                    "managers": serializers.IntegerField(),
                    "employees": serializers.IntegerField(),
                },
            ),
        },
    ),
)
@api_view(['GET'])
@permission_classes([CanViewAnalytics])
def manager_dashboard(request):
    """Compatibility alias for manager_overview"""
    return manager_overview(request)

# ---------- Manager: list employees/managers (no owners) ----------
class ManagerUserList(DefaultAuthMixin, generics.ListAPIView):
    serializer_class   = UserSerializer  # includes role (read-only)
    permission_classes = [IsManagerOrOwner]
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['username', 'email', 'first_name', 'last_name']

    def get_queryset(self):
        qs = User.objects.filter(is_superuser=False).order_by('id')
        role = self.request.query_params.get('role')
        if role in ('staff','manager'):
            qs = qs.filter(profile__role=role)
        return qs

# ---------- Manager: toggle active on employees only ----------
class ManagerUserDetail(DefaultAuthMixin, generics.RetrieveUpdateAPIView):
    queryset = User.objects.filter(is_superuser=False)
    serializer_class = ManagerUserSerializer
    permission_classes = [IsManagerOrOwner]

# ---------- NEW: Manager Charts Dashboard ----------

@staff_or_perm('manager_portal_access')
def manager_charts_dashboard(request):
    """
    Charts dashboard view for managers accessible at /manager/charts/
    Shows tasks by status, property, and task types with Chart.js visualizations
    """
    # Get tasks by status
    tasks_by_status = (
        Task.objects
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    
    # Get tasks by property
    tasks_by_property = (
        Task.objects
        .select_related('property_ref')
        .values('property_ref__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]  # Top 10 properties
    )
    
    # Get tasks by task type (Cleaning, Maintenance, etc.)
    tasks_by_type = (
        Task.objects
        .values('task_type')
        .annotate(count=Count('id'))
        .order_by('task_type')
    )
    
    # Get overdue tasks
    now = timezone.now()
    overdue_count = (
        Task.objects
        .filter(due_date__isnull=False, due_date__lt=now)
        .exclude(status__in=['completed', 'canceled'])
        .count()
    )
    
    # User Performance Analytics
    user_performance = (
        Task.objects
        .select_related('assigned_to')
        .values('assigned_to__username', 'assigned_to__first_name', 'assigned_to__last_name')
        .annotate(
            total_tasks=Count('id'),
            completed_tasks=Count('id', filter=Q(status='completed')),
            pending_tasks=Count('id', filter=Q(status='pending')),
            in_progress_tasks=Count('id', filter=Q(status='in-progress'))
        )
        .exclude(assigned_to__isnull=True)
        .order_by('-total_tasks')[:10]
    )
    
    # Task completion trends (last 30 days)
    from django.db.models.functions import TruncDate
    thirty_days_ago = now - timedelta(days=30)
    daily_completions = (
        Task.objects
        .filter(status='completed', modified_at__gte=thirty_days_ago)
        .annotate(day=TruncDate('modified_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    
    # User activity (tasks created/modified in last 7 days)
    seven_days_ago = now - timedelta(days=7)
    user_activity = (
        Task.objects
        .filter(modified_at__gte=seven_days_ago)
        .select_related('modified_by')
        .values('modified_by__username', 'modified_by__first_name', 'modified_by__last_name')
        .annotate(activity_count=Count('id'))
        .exclude(modified_by__isnull=True)
        .order_by('-activity_count')[:8]
    )
    
    # Prepare data for charts
    status_labels = []
    status_data = []
    status_colors = {
        'pending': '#f39c12',      # orange
        'in-progress': '#3498db',  # blue
        'completed': '#27ae60',    # green
        'canceled': '#e74c3c',     # red
    }
    
    for item in tasks_by_status:
        status_labels.append(item['status'].title())
        status_data.append(item['count'])
    
    property_labels = []
    property_data = []
    
    for item in tasks_by_property:
        property_name = item['property_ref__name'] or 'No Property'
        property_labels.append(property_name)
        property_data.append(item['count'])
    
    # Task type data
    type_labels = []
    type_data = []
    type_colors = {
        'cleaning': '#e74c3c',     # red
        'maintenance': '#f39c12',  # orange
        'inspection': '#9b59b6',   # purple
        'repair': '#34495e',       # dark blue
    }
    
    for item in tasks_by_type:
        type_labels.append(item['task_type'].replace('_', ' ').title())
        type_data.append(item['count'])
    
    # User performance data
    user_performance_labels = []
    user_performance_completed = []
    user_performance_total = []
    
    for user in user_performance:
        name = user['assigned_to__first_name'] or user['assigned_to__username']
        if user['assigned_to__last_name']:
            name += f" {user['assigned_to__last_name']}"
        user_performance_labels.append(name)
        user_performance_completed.append(user['completed_tasks'])
        user_performance_total.append(user['total_tasks'])
    
    # User activity data
    activity_labels = []
    activity_data = []
    
    for user in user_activity:
        name = user['modified_by__first_name'] or user['modified_by__username'] 
        if user['modified_by__last_name']:
            name += f" {user['modified_by__last_name']}"
        activity_labels.append(name)
        activity_data.append(user['activity_count'])
    
    # Total tasks
    total_tasks = Task.objects.count()
    
    context = {
        'title': 'Dashboard Charts',
        'total_tasks': total_tasks,
        'overdue_count': overdue_count,
        'active_users': len(user_performance_labels),
        'status_count': 4,  # Always 4 status types (pending, in-progress, completed, canceled)
        'property_count': len(property_labels),
        'task_type_count': len(type_labels),
        'status_chart_data': {
            'labels': json.dumps(status_labels),
            'data': json.dumps(status_data),
            'colors': json.dumps([status_colors.get(label.lower().replace(' ', '-'), '#95a5a6') for label in status_labels]),
        },
        'property_chart_data': {
            'labels': json.dumps(property_labels),
            'data': json.dumps(property_data),
        },
        'task_type_chart_data': {
            'labels': json.dumps(type_labels),
            'data': json.dumps(type_data),
            'colors': json.dumps([type_colors.get(item['task_type'], '#95a5a6') for item in tasks_by_type]),
        },
        'user_performance_chart_data': {
            'labels': json.dumps(user_performance_labels),
            'completed': json.dumps(user_performance_completed),
            'total': json.dumps(user_performance_total),
        },
        'user_activity_chart_data': {
            'labels': json.dumps(activity_labels),
            'data': json.dumps(activity_data),
        },
    }
    
    return render(request, 'admin/manager_charts.html', context)

@staff_or_perm('view_reports')
def admin_charts_dashboard(request):
    """
    Regular admin charts dashboard at /api/admin/charts/
    Shows same analytics but accessible to all Django admin users with view_reports permission
    """
    # Get tasks by status
    tasks_by_status = (
        Task.objects
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    
    # Get tasks by property
    tasks_by_property = (
        Task.objects
        .select_related('property_ref')
        .values('property_ref__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]  # Top 10 properties
    )
    
    # Get tasks by task type (Cleaning, Maintenance, etc.)
    tasks_by_type = (
        Task.objects
        .values('task_type')
        .annotate(count=Count('id'))
        .order_by('task_type')
    )
    
    # Get overdue tasks
    now = timezone.now()
    overdue_count = (
        Task.objects
        .filter(due_date__isnull=False, due_date__lt=now)
        .exclude(status__in=['completed', 'canceled'])
        .count()
    )
    
    # User Performance Analytics
    user_performance = (
        Task.objects
        .select_related('assigned_to')
        .values('assigned_to__username', 'assigned_to__first_name', 'assigned_to__last_name')
        .annotate(
            total_tasks=Count('id'),
            completed_tasks=Count('id', filter=Q(status='completed')),
            pending_tasks=Count('id', filter=Q(status='pending')),
            in_progress_tasks=Count('id', filter=Q(status='in-progress'))
        )
        .exclude(assigned_to__isnull=True)
        .order_by('-total_tasks')[:10]
    )
    
    # User activity (tasks created/modified in last 7 days)
    seven_days_ago = now - timedelta(days=7)
    user_activity = (
        Task.objects
        .filter(modified_at__gte=seven_days_ago)
        .select_related('modified_by')
        .values('modified_by__username', 'modified_by__first_name', 'modified_by__last_name')
        .annotate(activity_count=Count('id'))
        .exclude(modified_by__isnull=True)
        .order_by('-activity_count')[:8]
    )
    
    # Prepare data for charts
    status_labels = []
    status_data = []
    status_colors = {
        'pending': '#f39c12',      # orange
        'in-progress': '#3498db',  # blue
        'completed': '#27ae60',    # green
        'canceled': '#e74c3c',     # red
    }
    
    for item in tasks_by_status:
        status_labels.append(item['status'].title())
        status_data.append(item['count'])
    
    property_labels = []
    property_data = []
    
    for item in tasks_by_property:
        property_name = item['property_ref__name'] or 'No Property'
        property_labels.append(property_name)
        property_data.append(item['count'])
    
    # Task type data
    type_labels = []
    type_data = []
    type_colors = {
        'cleaning': '#e74c3c',     # red
        'maintenance': '#f39c12',  # orange
        'inspection': '#9b59b6',   # purple
        'repair': '#34495e',       # dark blue
    }
    
    for item in tasks_by_type:
        type_labels.append(item['task_type'].replace('_', ' ').title())
        type_data.append(item['count'])
    
    # User performance data
    user_performance_labels = []
    user_performance_completed = []
    user_performance_total = []
    
    for user in user_performance:
        name = user['assigned_to__first_name'] or user['assigned_to__username']
        if user['assigned_to__last_name']:
            name += f" {user['assigned_to__last_name']}"
        user_performance_labels.append(name)
        user_performance_completed.append(user['completed_tasks'])
        user_performance_total.append(user['total_tasks'])
    
    # User activity data
    activity_labels = []
    activity_data = []
    
    for user in user_activity:
        name = user['modified_by__first_name'] or user['modified_by__username'] 
        if user['modified_by__last_name']:
            name += f" {user['modified_by__last_name']}"
        activity_labels.append(name)
        activity_data.append(user['activity_count'])
    
    # Total tasks
    total_tasks = Task.objects.count()
    
    context = {
        'title': 'Admin Analytics Dashboard',
        'total_tasks': total_tasks,
        'overdue_count': overdue_count,
        'active_users': len(user_performance_labels),
        'status_count': 4,  # Always 4 status types (pending, in-progress, completed, canceled)
        'property_count': len(property_labels),
        'task_type_count': len(type_labels),
        'status_chart_data': {
            'labels': json.dumps(status_labels),
            'data': json.dumps(status_data),
            'colors': json.dumps([status_colors.get(label.lower().replace(' ', '-'), '#95a5a6') for label in status_labels]),
        },
        'property_chart_data': {
            'labels': json.dumps(property_labels),
            'data': json.dumps(property_data),
        },
        'task_type_chart_data': {
            'labels': json.dumps(type_labels),
            'data': json.dumps(type_data),
            'colors': json.dumps([type_colors.get(item['task_type'], '#95a5a6') for item in tasks_by_type]),
        },
        'user_performance_chart_data': {
            'labels': json.dumps(user_performance_labels),
            'completed': json.dumps(user_performance_completed),
            'total': json.dumps(user_performance_total),
        },
        'user_activity_chart_data': {
            'labels': json.dumps(activity_labels),
            'data': json.dumps(activity_data),
        },
    }
    
    return render(request, 'admin/charts_dashboard.html', context)


@staff_or_perm('system_metrics_access')
def system_metrics_dashboard(request):
    """
    System metrics and health dashboard for superusers and users with system_metrics_access permission
    Provides comprehensive system monitoring and performance insights
    """
    try:
        # Get comprehensive system metrics
        metrics = get_system_metrics()
        
        # Add request context
        metrics['request_info'] = {
            'user': request.user.username,
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'remote_addr': request.META.get('REMOTE_ADDR', 'Unknown'),
            'request_time': timezone.now().isoformat(),
        }
        
        # Configurable refresh intervals
        refresh_options = {
            'realtime': 5,    # 5 seconds - for critical monitoring
            'fast': 15,       # 15 seconds - for active monitoring  
            'normal': 30,     # 30 seconds - default balanced
            'slow': 60,       # 1 minute - for casual monitoring
            'manual': 0,      # Manual only - no auto-refresh
        }
        
        refresh_mode = request.GET.get('refresh', 'normal')
        refresh_interval = refresh_options.get(refresh_mode, 30)
        
        context = {
            'metrics': metrics,
            'refresh_interval': refresh_interval,
            'refresh_mode': refresh_mode,
            'refresh_options': refresh_options,
            'title': 'System Metrics Dashboard',
        }
        
        return render(request, 'admin/system_metrics.html', context)
        
    except Exception as e:
        context = {
            'error': str(e),
            'title': 'System Metrics Dashboard - Error',
        }
        return render(request, 'admin/system_metrics.html', context)


@staff_or_perm('system_metrics_access')
def system_metrics_api(request):
    """
    API endpoint for real-time system metrics (JSON)
    Used for dashboard auto-refresh
    """
    try:
        metrics = get_system_metrics()
        return JsonResponse(metrics)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def system_logs_viewer(request):
    """
    Log file viewer for superusers to examine system logs
    Provides search, filtering, and real-time viewing capabilities
    """
    # Only allow superusers to access logs
    if not request.user.is_superuser:
        raise DjangoPermissionDenied("Log viewer is only available to superusers.")
    
    import os
    
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    log_file = request.GET.get('file', 'debug.log')
    lines = int(request.GET.get('lines', 100))
    search = request.GET.get('search', '')
    level = request.GET.get('level', '')
    
    log_content = []
    available_files = []
    error_message = None
    
    try:
        # Get available log files
        if os.path.exists(log_dir):
            available_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            available_files.sort()
        
        # Read selected log file
        log_path = os.path.join(log_dir, log_file)
        if os.path.exists(log_path) and log_file in available_files:
            with open(log_path, 'r') as f:
                all_lines = f.readlines()
                
                # Apply filters
                filtered_lines = all_lines
                
                if search:
                    filtered_lines = [line for line in filtered_lines if search.lower() in line.lower()]
                
                if level:
                    filtered_lines = [line for line in filtered_lines if level.upper() in line]
                
                # Get last N lines
                log_content = filtered_lines[-lines:] if lines > 0 else filtered_lines
                
                # Add line numbers
                log_content = [
                    {
                        'number': len(all_lines) - len(filtered_lines) + i + 1,
                        'content': line.rstrip('\n'),
                        'level': _extract_log_level(line),
                    }
                    for i, line in enumerate(log_content)
                ]
        else:
            error_message = f"Log file '{log_file}' not found or not accessible."
            
    except Exception as e:
        error_message = f"Error reading log file: {str(e)}"
    
    context = {
        'log_content': log_content,
        'available_files': available_files,
        'current_file': log_file,
        'lines_shown': lines,
        'search_term': search,
        'level_filter': level,
        'error_message': error_message,
        'title': 'System Logs Viewer',
        'log_levels': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    }
    
    return render(request, 'admin/system_logs.html', context)


@login_required
def system_logs_download(request):
    """
    Download log files for superusers
    Supports downloading filtered logs with search and level filters
    """
    # Only allow superusers to download logs
    if not request.user.is_superuser:
        return HttpResponse("Log download is only available to superusers.", status=403)
    
    import os
    from django.http import HttpResponse
    
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    log_file = request.GET.get('file', 'debug.log')
    search = request.GET.get('search', '')
    level = request.GET.get('level', '')
    
    try:
        # Get available log files
        available_files = []
        if os.path.exists(log_dir):
            available_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        
        # Validate log file
        if log_file not in available_files:
            return HttpResponse(f"Log file '{log_file}' not found or not accessible.", status=404)
        
        # Read and filter log file
        log_path = os.path.join(log_dir, log_file)
        with open(log_path, 'r') as f:
            all_lines = f.readlines()
            
            # Apply filters
            filtered_lines = all_lines
            
            if search:
                filtered_lines = [line for line in filtered_lines if search.lower() in line.lower()]
            
            if level:
                filtered_lines = [line for line in filtered_lines if level.upper() in line]
            
            # Join filtered lines
            log_content = ''.join(filtered_lines)
        
        # Create filename with timestamp and filters
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename_parts = [log_file.replace('.log', ''), timestamp]
        
        if search:
            filename_parts.append(f'search_{search[:20]}')
        if level:
            filename_parts.append(f'level_{level.lower()}')
        
        filename = f"{'_'.join(filename_parts)}.log"
        
        # Create response
        response = HttpResponse(log_content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(log_content.encode('utf-8'))
        
        return response
        
    except Exception as e:
        return HttpResponse(f"Error downloading log file: {str(e)}", status=500)


def _extract_log_level(log_line):
    """Extract log level from a log line for color coding"""
    log_line_upper = log_line.upper()
    if 'ERROR' in log_line_upper:
        return 'ERROR'
    elif 'WARNING' in log_line_upper or 'WARN' in log_line_upper:
        return 'WARNING'
    elif 'INFO' in log_line_upper:
        return 'INFO'
    elif 'DEBUG' in log_line_upper:
        return 'DEBUG'
    elif 'CRITICAL' in log_line_upper:
        return 'CRITICAL'
    return 'UNKNOWN'


@login_required
def system_crash_recovery(request):
    """
    System crash recovery and diagnostic information
    Helps superusers understand and recover from system failures
    """
    # Only allow superusers
    if not request.user.is_superuser:
        raise DjangoPermissionDenied("Crash recovery is only available to superusers.")
    
    import os
    import subprocess
    
    recovery_info = {
        'system_status': 'operational',
        'recent_errors': [],
        'recovery_suggestions': [],
        'diagnostic_info': {},
    }
    
    try:
        # Check for recent errors in error log
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        error_log_path = os.path.join(log_dir, 'error.log')
        
        if os.path.exists(error_log_path):
            with open(error_log_path, 'r') as f:
                recent_lines = f.readlines()[-50:]  # Last 50 error lines
                recovery_info['recent_errors'] = [
                    {
                        'line': line.strip(),
                        'level': _extract_log_level(line),
                        'timestamp': _extract_timestamp(line),
                    }
                    for line in recent_lines if line.strip()
                ]
        
        # System diagnostic information
        try:
            # Check if server process is responsive
            import psutil
            current_process = psutil.Process()
            
            recovery_info['diagnostic_info'] = {
                'process_status': 'running',
                'memory_usage_mb': round(current_process.memory_info().rss / 1024 / 1024, 2),
                'cpu_usage_percent': current_process.cpu_percent(),
                'open_files': len(current_process.open_files()),
                'connections': len(current_process.connections()),
                'threads': current_process.num_threads(),
            }
        except Exception as e:
            recovery_info['diagnostic_info']['error'] = str(e)
        
        # Generate recovery suggestions based on errors
        error_keywords = [line['line'].lower() for line in recovery_info['recent_errors']]
        suggestions = []
        
        if any('memory' in error or 'out of memory' in error for error in error_keywords):
            suggestions.append("🔧 High memory usage detected - consider restarting the server")
            suggestions.append("💾 Check for memory leaks in recent code changes")
            
        if any('database' in error or 'connection' in error for error in error_keywords):
            suggestions.append("🗄️ Database connection issues - check database server status")
            suggestions.append("🔌 Verify database credentials and network connectivity")
            
        if any('permission' in error or 'access denied' in error for error in error_keywords):
            suggestions.append("🔐 Permission issues - check file and directory permissions")
            suggestions.append("👤 Verify user account has required system access")
            
        if any('disk' in error or 'space' in error for error in error_keywords):
            suggestions.append("💿 Disk space issues - clean up log files and temporary data")
            suggestions.append("📊 Monitor disk usage in system metrics")
            
        if not suggestions:
            suggestions.append("✅ No critical issues detected in recent logs")
            suggestions.append("📊 Monitor system metrics for performance trends")
            
        recovery_info['recovery_suggestions'] = suggestions
        
        # Determine overall system status
        critical_errors = len([e for e in recovery_info['recent_errors'] if e['level'] in ['ERROR', 'CRITICAL']])
        if critical_errors > 10:
            recovery_info['system_status'] = 'critical'
        elif critical_errors > 3:
            recovery_info['system_status'] = 'warning'
        else:
            recovery_info['system_status'] = 'operational'
            
    except Exception as e:
        recovery_info['system_status'] = 'error'
        recovery_info['error'] = str(e)
    
    context = {
        'recovery_info': recovery_info,
        'title': 'System Crash Recovery',
    }
    
    return render(request, 'admin/system_recovery.html', context)


def _extract_timestamp(log_line):
    """Extract timestamp from log line if possible"""
    import re
    # Look for common timestamp patterns
    timestamp_patterns = [
        r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
        r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',
    ]
    
    for pattern in timestamp_patterns:
        match = re.search(pattern, log_line)
        if match:
            return match.group()
    
    return 'Unknown'


# ----------------------------------------------------------------------------
# Excel Import Views
# ----------------------------------------------------------------------------

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect  # render/JsonResponse/csrf_exempt/require_http_methods already imported above
from django.contrib import messages
from .services.excel_import_service import ExcelImportService

def is_superuser_or_manager(user):
    """Check if user is superuser or manager"""
    return user.is_superuser or (hasattr(user, 'profile') and user.profile.role in [UserRole.MANAGER, UserRole.SUPERUSER])

@login_required
@user_passes_test(is_superuser_or_manager)
def excel_import_view(request):
    """View for importing Excel booking schedules"""
    
    logger.info(f"Excel import view accessed by user: {request.user.username}")
    
    if request.method == 'POST':
        try:
            excel_file = request.FILES.get('excel_file')
            if not excel_file:
                logger.warning(f"User {request.user.username} attempted import without selecting a file")
                messages.error(request, 'Please select an Excel file to import.')
                return redirect('excel-import')
            
            logger.info(f"User {request.user.username} uploading file: {excel_file.name} ({excel_file.size} bytes)")
            
            # Check file extension
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                logger.warning(f"User {request.user.username} uploaded invalid file type: {excel_file.name}")
                messages.error(request, 'Please upload a valid Excel file (.xlsx or .xls)')
                return redirect('excel-import')
            
            # Create default import template
            template = None
            first_property = Property.objects.first()
            if first_property:
                template, created = BookingImportTemplate.objects.get_or_create(
                    name="Default Import Template",
                    property_ref=first_property,
                    defaults={
                        'import_type': 'csv',
                        'auto_create_tasks': True,
                        'created_by': request.user
                    }
                )
                if created:
                    logger.info(f"Created new import template for user {request.user.username}")
            
            # Process the Excel file
            logger.info(f"Starting Excel import for user {request.user.username} with file: {excel_file.name}")
            import_service = ExcelImportService(request.user, template)
            result = import_service.import_excel_file(excel_file)
            
            if result['success']:
                logger.info(f"Excel import successful for user {request.user.username}: {result['successful_imports']} bookings, {result['errors_count']} errors, {result['warnings_count']} warnings")
                
                messages.success(
                    request, 
                    f"Import completed successfully! {result['successful_imports']} bookings processed. "
                    f"Errors: {result['errors_count']}, Warnings: {result['warnings_count']}"
                )
                
                if result['errors']:
                    for error in result['errors'][:5]:  # Show first 5 errors
                        messages.warning(request, f"Error: {error}")
                    
                    if len(result['errors']) > 5:
                        messages.warning(request, f"... and {len(result['errors']) - 5} more errors. Check the import log for details.")
                
                # Display warnings to user
                if result.get('warnings_count', 0) > 0:
                    warnings_list = result.get('warnings', [])
                    if warnings_list:
                        # Show first few warnings
                        display_warnings = warnings_list[:5]
                        for warning in display_warnings:
                            messages.warning(request, f"⚠️ {warning}")
                        
                        if len(warnings_list) > 5:
                            messages.warning(request, f"⚠️ ... and {len(warnings_list) - 5} more warnings. Check import log for full details.")
                    else:
                        messages.warning(request, f"Import completed with {result['warnings_count']} warnings. Check the import log for details.")
                
                if result.get('new_properties_created', 0) > 0:
                    new_properties_list = result.get('new_properties_list', [])
                    if new_properties_list:
                        messages.success(
                            request, 
                            f"🎉 Successfully created {result['new_properties_created']} new properties: "
                            f"{', '.join(new_properties_list[:5])}{'...' if len(new_properties_list) > 5 else ''}"
                        )
                    else:
                        messages.success(request, f"🎉 Created {result['new_properties_created']} new properties during import.")
                
            elif result.get('requires_property_approval'):
                # Handle new properties that need admin approval
                new_properties = result.get('new_properties', [])
                if request.user.is_superuser:
                    # Admin can see the properties and choose to create them
                    context = {
                        'requires_approval': True,
                        'new_properties': new_properties,
                        'excel_file': excel_file,
                        'title': 'New Properties Require Approval'
                    }
                    return render(request, 'admin/property_approval.html', context)
                else:
                    # Manager gets a message about contacting admin
                    messages.warning(
                        request, 
                        f"Import requires admin approval. Found {len(new_properties)} new properties: "
                        f"{', '.join(new_properties[:5])}{'...' if len(new_properties) > 5 else ''}. "
                        f"Please contact an administrator."
                    )
            else:
                messages.error(request, f"Import failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Excel import exception for user {request.user.username}: {str(e)}", exc_info=True)
            messages.error(request, f"Import failed: {str(e)}")
    
    # Get recent import logs
    recent_imports = []
    if hasattr(request.user, 'profile') and request.user.profile.role in ['manager', 'superuser']:
        recent_imports = BookingImportLog.objects.filter(
            imported_by=request.user
        ).order_by('-imported_at')[:10]
    
    context = {
        'recent_imports': recent_imports,
        'title': 'Import Booking Schedule',
    }
    
    return render(request, 'admin/excel_import.html', context)


@login_required
@user_passes_test(is_superuser_or_manager)
def excel_import_api(request):
    """API endpoint for Excel import (for AJAX requests)"""
    logger.info(f"Excel import API accessed by user: {request.user.username}")
    
    if request.method != 'POST':
        logger.warning(f"User {request.user.username} attempted to access Excel import API with {request.method} method")
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            logger.warning(f"User {request.user.username} attempted Excel import without providing a file")
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        logger.info(f"User {request.user.username} uploading file via API: {excel_file.name} ({excel_file.size} bytes)")
        
        # Process the Excel file
        import_service = ExcelImportService(request.user)
        result = import_service.import_excel_file(excel_file)
        
        logger.info(f"Excel import API result for user {request.user.username}: success={result.get('success')}, bookings={result.get('successful_imports', 0)}")
        
        # If properties need approval, return special response
        if result.get('requires_property_approval'):
            result['message'] = f"Import requires admin approval. Found {len(result.get('new_properties', []))} new properties."
            logger.info(f"Excel import requires property approval for user {request.user.username}: {len(result.get('new_properties', []))} new properties")
        
        # Add success message for new properties created
        if result.get('new_properties_created', 0) > 0:
            new_properties_list = result.get('new_properties_list', [])
            if new_properties_list:
                result['success_message'] = f"🎉 Successfully created {result['new_properties_created']} new properties: {', '.join(new_properties_list[:5])}{'...' if len(new_properties_list) > 5 else ''}"
            else:
                result['success_message'] = f"🎉 Created {result['new_properties_created']} new properties during import."
            logger.info(f"Excel import created {result['new_properties_created']} new properties for user {request.user.username}")
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Excel import API exception for user {request.user.username}: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def property_approval_create(request):
    """Handle property approval and creation for admins"""
    if request.method != 'POST':
        return redirect('excel-import')
    
    try:
        approved_properties = request.POST.getlist('approved_properties')
        excel_file_name = request.POST.get('excel_file')
        
        if not approved_properties:
            messages.warning(request, 'No properties were selected for creation.')
            return redirect('excel-import')
        
        # Create the approved properties
        created_count = 0
        for property_name in approved_properties:
            try:
                Property.objects.create(
                    name=property_name.strip(),
                    created_by=request.user,
                    modified_by=request.user
                )
                created_count += 1
                logger.info(f"Admin {request.user.username} created property: {property_name}")
            except Exception as e:
                logger.error(f"Failed to create property {property_name}: {e}")
                messages.error(request, f"Failed to create property '{property_name}': {str(e)}")
        
        if created_count > 0:
            messages.success(request, f"Successfully created {created_count} new properties.")
            
            # Now try to import the Excel file again
            # Note: In a real implementation, you'd want to store the file temporarily
            # For now, we'll redirect back to the import page
            messages.info(request, f"Please upload your Excel file again to continue with the import.")
        
        return redirect('excel-import')
        
    except Exception as e:
        messages.error(request, f"Property approval failed: {str(e)}")
        logger.error(f"Property approval error: {e}")
        return redirect('excel-import')


# =============================================================================
# ENHANCED EXCEL IMPORT WITH CONFLICT RESOLUTION
# =============================================================================

from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .services.enhanced_excel_import_service import (
    EnhancedExcelImportService, ConflictResolutionService
)


class ConflictReviewView(LoginRequiredMixin, View):
    """View for reviewing booking conflicts from Excel import"""
    
    def get(self, request, import_session_id):
        """Display conflict resolution interface"""
        try:
            import_log = BookingImportLog.objects.get(id=import_session_id)
            
            # Extract conflicts data from import log using utility function
            conflicts_data = extract_conflicts_json(import_log.errors_log)
            
            context = {
                'import_log': import_log,
                'conflicts': conflicts_data,
                'import_session_id': import_session_id
            }
            
            return render(request, 'admin/conflict_resolution.html', context)
            
        except BookingImportLog.DoesNotExist:
            return JsonResponse({'error': 'Import session not found'}, status=404)
        except Exception as e:
            logger.error(f"Error loading conflicts: {str(e)}")
            return JsonResponse({'error': 'Failed to load conflicts'}, status=500)


# (login_required, csrf_exempt, JsonResponse, json) already imported at top

@csrf_exempt
@login_required
def resolve_conflicts(request, import_session_id):
    """Resolve conflicts based on user decisions"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        resolutions = data.get('resolutions', [])
        
        if not resolutions:
            return JsonResponse({'error': 'No resolutions provided'}, status=400)
        
        # Use conflict resolution service
        resolution_service = ConflictResolutionService(request.user)
        results = resolution_service.resolve_conflicts(import_session_id, resolutions)
        
        return JsonResponse({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Failed to resolve conflicts: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
def get_conflict_details(request, import_session_id):
    """Get detailed conflict information for AJAX requests"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        import_log = BookingImportLog.objects.get(id=import_session_id)
        
        # Extract conflicts data with robust JSON parsing using utility function
        conflicts_data = extract_conflicts_json(import_log.errors_log)
        
        return JsonResponse({
            'success': True,
            'conflicts': conflicts_data,
            'import_info': {
                'import_file': str(import_log.import_file) if import_log.import_file else 'Unknown',
                'imported_at': import_log.imported_at.isoformat(),
                'total_rows': import_log.total_rows,
                'successful_imports': import_log.successful_imports,
                'errors_count': import_log.errors_count
            }
        })
        
    except BookingImportLog.DoesNotExist:
        return JsonResponse({'error': 'Import session not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting conflict details: {str(e)}")
        return JsonResponse({'error': 'Failed to get conflict details'}, status=500)


@staff_or_perm('manage_bookings')
@require_http_methods(["GET"])
def preview_conflict_resolution(request, import_session_id, conflict_index):
    """Preview what changes would be made for a specific conflict resolution"""
    try:
        import_log = BookingImportLog.objects.get(id=import_session_id)
        
        # Extract specific conflict
        conflicts_data = []
        if "CONFLICTS_DATA:" in import_log.errors_log:
            conflicts_json = import_log.errors_log.split("CONFLICTS_DATA:")[1]
            conflicts_data = json.loads(conflicts_json)
        
        if int(conflict_index) >= len(conflicts_data):
            return JsonResponse({'error': 'Conflict not found'}, status=404)
        
        conflict = conflicts_data[int(conflict_index)]
        existing_booking = Booking.objects.get(id=conflict['existing_booking']['id'])
        
        # Prepare preview data
        preview = {
            'existing_booking': {
                'id': existing_booking.pk,
                'external_code': existing_booking.external_code,
                'guest_name': existing_booking.guest_name,
                'check_in_date': existing_booking.check_in_date.strftime('%Y-%m-%d'),
                'check_out_date': existing_booking.check_out_date.strftime('%Y-%m-%d'),
                'status': existing_booking.status,
                'external_status': existing_booking.external_status,
                'source': existing_booking.source,
                'property_name': existing_booking.property.name
            },
            'excel_data': conflict['excel_data'],
            'changes_summary': conflict['changes_summary'],
            'conflict_types': conflict['conflict_types'],
            'confidence_score': conflict['confidence_score']
        }
        
        return JsonResponse({
            'success': True,
            'preview': preview
        })
        
    except Exception as e:
        logger.error(f"Error previewing conflict resolution: {str(e)}")
        return JsonResponse({'error': 'Failed to preview conflict'}, status=500)


@staff_or_perm('manage_bookings')
@require_http_methods(["POST"])
@csrf_exempt
def quick_resolve_conflict(request, import_session_id, conflict_index):
    """Quick resolve a single conflict with predefined actions"""
    try:
        data = json.loads(request.body)
        action = data.get('action')  # 'auto_update', 'create_new', 'skip'
        
        if action not in ['auto_update', 'create_new', 'skip']:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
        # Map quick actions to full resolution format
        if action == 'auto_update':
            resolution = {
                'conflict_index': int(conflict_index),
                'action': 'update_existing',
                'apply_changes': ['guest_name', 'dates', 'status']  # Update all changes
            }
        elif action == 'create_new':
            resolution = {
                'conflict_index': int(conflict_index),
                'action': 'create_new',
                'apply_changes': []
            }
        else:  # skip
            resolution = {
                'conflict_index': int(conflict_index),
                'action': 'skip',
                'apply_changes': []
            }
        
        # Resolve using service
        resolution_service = ConflictResolutionService(request.user)
        results = resolution_service.resolve_conflicts(import_session_id, [resolution])
        
        return JsonResponse({
            'success': True,
            'action': action,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in quick resolve: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@staff_or_perm('manage_bookings')
def enhanced_excel_import_view(request):
    """Enhanced Excel import view with conflict detection"""
    
    # GPT Agent Fix: Enhanced import access validation and logging
    logger.info(f"Enhanced Excel import accessed by {request.user.username} (role={getattr(request.user.profile, 'role', 'unknown')}, superuser={request.user.is_superuser})")
    
    # Additional validation: Ensure user has active profile
    if not hasattr(request.user, 'profile') and not request.user.is_superuser:
        logger.warning(f"User {request.user.username} attempted import without proper profile setup")
        messages.error(request, 'Your account is not properly configured for Excel imports. Contact an administrator.')
        return redirect('admin:index')
    
    if request.method == 'POST':
        # Handle file upload and processing
        excel_file = request.FILES.get('excel_file')
        sheet_name = request.POST.get('sheet_name', 'Cleaning schedule')
        
        if not excel_file:
            logger.warning(f"User {request.user.username} attempted import without file")
            messages.error(request, 'Please select an Excel file to upload.')
            return render(request, 'admin/enhanced_excel_import.html')
        
        # Validate file size (prevent huge uploads)
        max_size = 10 * 1024 * 1024  # 10MB limit
        if excel_file.size > max_size:
            logger.warning(f"User {request.user.username} attempted to upload oversized file: {excel_file.size} bytes")
            messages.error(request, 'File too large. Maximum size is 10MB.')
            return render(request, 'admin/enhanced_excel_import.html')
        
        logger.info(f"User {request.user.username} starting import of {excel_file.name} ({excel_file.size} bytes)")
        
        try:
            # Use enhanced import service
            enhanced_service = EnhancedExcelImportService(request.user)
            result = enhanced_service.import_excel_file(excel_file, sheet_name)
            
            if result['success']:
                # Check for conflicts requiring review
                if result.get('requires_review') and result.get('conflicts_detected', 0) > 0:
                    # Redirect to conflict resolution page
                    messages.warning(
                        request, 
                        f"Import completed with {result['conflicts_detected']} conflicts requiring manual review. "
                        f"{result['successful_imports']} bookings imported successfully, "
                        f"{result['auto_updated']} bookings auto-updated."
                    )
                    
                    conflict_review_url = reverse('conflict-review', args=[result['import_session_id']])
                    return redirect(conflict_review_url)
                else:
                    # No conflicts - standard success
                    messages.success(
                        request,
                        f"Excel import completed successfully! "
                        f"{result['successful_imports']} bookings imported, "
                        f"{result['auto_updated']} bookings auto-updated. "
                        f"No conflicts detected."
                    )
            else:
                messages.error(request, f"Import failed: {result.get('error', 'Unknown error')}")
                
                # Show errors if any
                if result.get('errors'):
                    for error in result['errors'][:5]:  # Show first 5 errors
                        messages.error(request, f"Row error: {error}")
                        
        except Exception as e:
            logger.error(f"Enhanced Excel import failed: {str(e)}")
            messages.error(request, f"Import failed: {str(e)}")
    
    # Get available templates for the form
    templates = BookingImportTemplate.objects.all()
    
    context = {
        'templates': templates,
        'title': 'Enhanced Excel Import with Conflict Resolution'
    }
    
    return render(request, 'admin/enhanced_excel_import.html', context)


@staff_or_perm('manage_bookings')
def enhanced_excel_import_api(request):
    """Enhanced Excel import API endpoint"""
    
    # GPT Agent Fix: Enhanced import access validation and logging
    logger.info(f"Enhanced Excel import API accessed by {request.user.username} (role={getattr(request.user.profile, 'role', 'unknown')}, superuser={request.user.is_superuser})")
    
    if request.method != 'POST':
        logger.warning(f"User {request.user.username} attempted non-POST access to import API")
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    # Additional validation: Ensure user has active profile
    if not hasattr(request.user, 'profile') and not request.user.is_superuser:
        logger.warning(f"User {request.user.username} attempted API import without proper profile setup")
        return JsonResponse({'success': False, 'error': 'Account not properly configured for imports'})
    
    excel_file = request.FILES.get('excel_file')
    sheet_name = request.POST.get('sheet_name', 'Cleaning schedule')
    
    if not excel_file:
        logger.warning(f"User {request.user.username} attempted API import without file")
        return JsonResponse({'success': False, 'error': 'No Excel file provided'})
    
    # Validate file size (prevent huge uploads)
    max_size = 10 * 1024 * 1024  # 10MB limit
    if excel_file.size > max_size:
        logger.warning(f"User {request.user.username} attempted to upload oversized file via API: {excel_file.size} bytes")
        return JsonResponse({'success': False, 'error': 'File too large. Maximum size is 10MB.'})
    
    logger.info(f"User {request.user.username} starting API import of {excel_file.name} ({excel_file.size} bytes)")
    
    try:
        # Use enhanced import service
        enhanced_service = EnhancedExcelImportService(request.user)
        result = enhanced_service.import_excel_file(excel_file, sheet_name)
        
        # Add conflict resolution URL if conflicts detected
        if result.get('requires_review') and result.get('import_session_id'):
            result['conflict_review_url'] = reverse('conflict-review', args=[result['import_session_id']])
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Enhanced Excel import API failed: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@staff_or_perm('manage_files')
@require_http_methods(["GET", "POST"])
def file_cleanup_api(request):
    """
    API endpoint for Excel import file cleanup management.
    
    GET: Returns current storage statistics
    POST: Performs cleanup operations based on parameters
    
    POST Parameters:
    - action: 'stats', 'suggest', 'dry_run', or 'cleanup'
    - days: Number of days to keep (for dry_run and cleanup actions)
    - target_mb: Target size in MB (for suggest action)
    """
    from .services.file_cleanup_service import ImportFileCleanupService
    
    # Remove DRF-specific permission check since @staff_or_perm handles it
    
    if request.method == 'GET':
        # Return current storage statistics
        stats = ImportFileCleanupService.get_storage_stats()
        return JsonResponse({
            'success': True,
            'stats': stats
        })
    
    elif request.method == 'POST':
        # Handle JSON data from the frontend
        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            # Fallback to POST data
            data = request.POST
            
        action = data.get('action', 'stats')
        
        try:
            if action == 'stats':
                stats = ImportFileCleanupService.get_storage_stats()
                return JsonResponse({
                    'success': True,
                    'action': 'stats',
                    'stats': stats
                })
            
            elif action == 'suggest':
                target_mb = int(data.get('target_mb', 100))
                suggestion = ImportFileCleanupService.suggest_cleanup(target_mb)
                return JsonResponse({
                    'success': True,
                    'action': 'suggest',
                    'suggestion': suggestion
                })
            
            elif action in ['dry_run', 'cleanup']:
                days = int(data.get('days', 30))
                dry_run = (action == 'dry_run')
                
                result = ImportFileCleanupService.cleanup_old_files(days, dry_run)
                
                return JsonResponse({
                    'success': True,
                    'action': action,
                    'result': result
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Unknown action: {action}'
                }, status=400)
        
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid parameter: {str(e)}'
            }, status=400)
        
        except Exception as e:
            logger.error(f"File cleanup API error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


# ========== PERMISSION MANAGEMENT API ==========

@extend_schema(
    operation_id="user_permissions",
    summary="Get current user's permissions",
    responses=inline_serializer(
        name="UserPermissionsResponse",
        fields={
            "user": serializers.CharField(),
            "role": serializers.CharField(),
            "permissions": serializers.DictField(child=serializers.BooleanField()),
            "delegatable_permissions": serializers.ListField(child=serializers.CharField()),
        },
    ),
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_permissions(request):
    """
    Get current user's permissions
    """
    try:
        if not hasattr(request.user, 'profile'):
            return Response({
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        profile = request.user.profile
        permissions = profile.get_all_permissions()
        delegatable = list(profile.get_delegatable_permissions())
        
        return Response({
            'user': request.user.username,
            'role': profile.role,
            'permissions': permissions,
            'delegatable_permissions': delegatable
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    operation_id="available_permissions",
    summary="List permissions visible/manageable to current user",
    responses=inline_serializer(
        name="AvailablePermissionsResponse",
        fields={
            "permissions": serializers.ListField(
                child=inline_serializer(
                    name="PermissionItem",
                    fields={
                        "name": serializers.CharField(),
                        "display_name": serializers.CharField(),
                        "description": serializers.CharField(allow_blank=True, required=False),
                        "can_delegate": serializers.BooleanField(),
                    },
                )
            )
        },
    ),
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_permissions(request):
    """
    Get all available permissions that the current user can see/manage
    """
    try:
        if not hasattr(request.user, 'profile'):
            return Response({
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        profile = request.user.profile
        
        # Superusers can see all permissions
        if profile.role == UserRole.SUPERUSER:
            permissions = CustomPermission.objects.filter(is_active=True)
        else:
            # Others can only see permissions they can delegate
            delegatable = profile.get_delegatable_permissions()
            permissions = CustomPermission.objects.filter(
                name__in=delegatable,
                is_active=True
            )
        
        permissions_data = []
        for perm in permissions:
            permissions_data.append({
                'name': perm.name,
                'display_name': perm.get_name_display(),
                'description': perm.description,
                'can_delegate': profile.can_delegate_permission(perm.name)
            })
        
        return Response({
            'permissions': permissions_data
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    operation_id="manageable_users",
    summary="Users current user can manage",
    responses=inline_serializer(
        name="ManageableUsersResponse",
        fields={
            "users": serializers.ListField(
                child=inline_serializer(
                    name="ManageableUser",
                    fields={
                        "id": serializers.IntegerField(),
                        "username": serializers.CharField(),
                        "email": serializers.EmailField(),
                        "first_name": serializers.CharField(allow_blank=True),
                        "last_name": serializers.CharField(allow_blank=True),
                        "role": serializers.CharField(),
                        "permissions": serializers.DictField(child=serializers.BooleanField()),
                    },
                )
            )
        },
    ),
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def manageable_users(request):
    """
    Get users that the current user can manage permissions for
    """
    try:
        if not hasattr(request.user, 'profile'):
            return Response({
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        profile = request.user.profile
        
        # Define role hierarchy: superuser > manager > staff
        role_hierarchy = {
            UserRole.SUPERUSER: [UserRole.MANAGER, UserRole.STAFF, UserRole.VIEWER],
            UserRole.MANAGER: [UserRole.STAFF, UserRole.VIEWER],
            UserRole.STAFF: [],
            UserRole.VIEWER: []
        }
        
        manageable_roles = role_hierarchy.get(profile.role, [])
        
        # Get users with manageable roles
        users = User.objects.filter(
            profile__role__in=manageable_roles,
            is_active=True
        ).select_related('profile')
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.profile.role if hasattr(user, 'profile') else 'staff',
                'permissions': user.profile.get_all_permissions() if hasattr(user, 'profile') else {}
            })
        
        return Response({
            'users': users_data
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    operation_id="grant_permission",
    summary="Grant a permission to a user",
    request=inline_serializer(
        name="GrantPermissionRequest",
        fields={
            "user_id": serializers.IntegerField(),
            "permission": serializers.CharField(),
            "reason": serializers.CharField(required=False, allow_blank=True),
            "expires_at": serializers.DateTimeField(required=False),
        },
    ),
    responses=inline_serializer(
        name="GrantPermissionResponse",
        fields={
            "success": serializers.BooleanField(),
            "message": serializers.CharField(),
            "override_id": serializers.IntegerField(),
            "created": serializers.BooleanField(),
        },
    ),
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def grant_permission(request):
    """
    Grant a permission to a user
    """
    try:
        if not hasattr(request.user, 'profile'):
            return Response({
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        profile = request.user.profile
        target_user_id = request.data.get('user_id')
        permission_name = request.data.get('permission')
        reason = request.data.get('reason', '')
        expires_at = request.data.get('expires_at')  # Optional
        
        if not target_user_id or not permission_name:
            return Response({
                'error': 'user_id and permission are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if current user can delegate this permission
        if not profile.can_delegate_permission(permission_name):
            return Response({
                'error': 'You do not have permission to delegate this permission'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get target user
        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response({
                'error': 'Target user not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if target user is manageable by current user
        if not hasattr(target_user, 'profile'):
            return Response({
                'error': 'Target user has no profile'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        target_role = target_user.profile.role
        current_role = profile.role
        
        # Role hierarchy check
        role_hierarchy = {
            UserRole.SUPERUSER: [UserRole.MANAGER, UserRole.STAFF, UserRole.VIEWER],
            UserRole.MANAGER: [UserRole.STAFF, UserRole.VIEWER],
        }
        
        manageable_roles = role_hierarchy.get(current_role, [])
        if target_role not in manageable_roles:
            return Response({
                'error': 'You cannot manage permissions for this user'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get permission object
        try:
            permission_obj = CustomPermission.objects.get(name=permission_name, is_active=True)
        except CustomPermission.DoesNotExist:
            return Response({
                'error': 'Permission not found or inactive'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Parse expires_at if provided
        expires_datetime = None
        if expires_at:
            from datetime import datetime
            try:
                expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            except ValueError:
                return Response({
                    'error': 'Invalid expires_at format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or update permission override
        override, created = UserPermissionOverride.objects.update_or_create(
            user=target_user,
            permission=permission_obj,
            defaults={
                'granted': True,
                'granted_by': request.user,
                'reason': reason,
                'expires_at': expires_datetime
            }
        )
        
        return Response({
            'success': True,
            'message': f'Permission {permission_obj.get_name_display()} granted to {target_user.username}',
            'override_id': override.id,
            'created': created
        })
    
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    operation_id="revoke_permission",
    summary="Revoke a permission from a user",
    request=inline_serializer(
        name="RevokePermissionRequest",
        fields={
            "user_id": serializers.IntegerField(),
            "permission": serializers.CharField(),
            "reason": serializers.CharField(required=False, allow_blank=True),
        },
    ),
    responses=inline_serializer(
        name="RevokePermissionResponse",
        fields={
            "success": serializers.BooleanField(),
            "message": serializers.CharField(),
            "override_id": serializers.IntegerField(),
            "created": serializers.BooleanField(),
        },
    ),
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_permission(request):
    """
    Revoke a permission from a user
    """
    try:
        if not hasattr(request.user, 'profile'):
            return Response({
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        profile = request.user.profile
        target_user_id = request.data.get('user_id')
        permission_name = request.data.get('permission')
        reason = request.data.get('reason', '')
        
        if not target_user_id or not permission_name:
            return Response({
                'error': 'user_id and permission are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if current user can delegate this permission
        if not profile.can_delegate_permission(permission_name):
            return Response({
                'error': 'You do not have permission to manage this permission'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get target user
        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response({
                'error': 'Target user not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check role hierarchy (same as grant_permission)
        if not hasattr(target_user, 'profile'):
            return Response({
                'error': 'Target user has no profile'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        target_role = target_user.profile.role
        current_role = profile.role
        
        role_hierarchy = {
            UserRole.SUPERUSER: [UserRole.MANAGER, UserRole.STAFF, UserRole.VIEWER],
            UserRole.MANAGER: [UserRole.STAFF, UserRole.VIEWER],
        }
        
        manageable_roles = role_hierarchy.get(current_role, [])
        if target_role not in manageable_roles:
            return Response({
                'error': 'You cannot manage permissions for this user'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get permission object
        try:
            permission_obj = CustomPermission.objects.get(name=permission_name, is_active=True)
        except CustomPermission.DoesNotExist:
            return Response({
                'error': 'Permission not found or inactive'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create or update permission override to deny
        override, created = UserPermissionOverride.objects.update_or_create(
            user=target_user,
            permission=permission_obj,
            defaults={
                'granted': False,
                'granted_by': request.user,
                'reason': reason,
                'expires_at': None  # Revocations don't expire
            }
        )
        
        return Response({
            'success': True,
            'message': f'Permission {permission_obj.get_name_display()} revoked from {target_user.username}',
            'override_id': override.id,
            'created': created
        })
    
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    operation_id="remove_permission_override",
    summary="Remove a permission override (revert to role-based permission)",
    request=inline_serializer(
        name="RemovePermissionOverrideRequest",
        fields={
            "user_id": serializers.IntegerField(),
            "permission_name": serializers.CharField(),
        },
    ),
    responses=inline_serializer(
        name="RemovePermissionOverrideResponse",
        fields={
            "success": serializers.BooleanField(),
            "message": serializers.CharField(),
        },
    ),
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_permission_override(request):
    """
    Remove a permission override (revert to role-based permission)
    """
    try:
        if not hasattr(request.user, 'profile'):
            return Response({
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        profile = request.user.profile
        target_user_id = request.data.get('user_id')
        permission_name = request.data.get('permission')
        
        if not target_user_id or not permission_name:
            return Response({
                'error': 'user_id and permission are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if current user can delegate this permission
        if not profile.can_delegate_permission(permission_name):
            return Response({
                'error': 'You do not have permission to manage this permission'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get target user
        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response({
                'error': 'Target user not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get permission object
        try:
            permission_obj = CustomPermission.objects.get(name=permission_name, is_active=True)
        except CustomPermission.DoesNotExist:
            return Response({
                'error': 'Permission not found or inactive'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Remove override if it exists
        try:
            override = UserPermissionOverride.objects.get(
                user=target_user,
                permission=permission_obj
            )
            override.delete()
            return Response({
                'success': True,
                'message': f'Permission override removed. {target_user.username} now has role-based access to {permission_obj.get_name_display()}'
            })
        except UserPermissionOverride.DoesNotExist:
            return Response({
                'success': True,
                'message': 'No override existed for this permission'
            })
    
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@staff_or_perm('manage_permissions')
def permission_management_view(request):
    """
    Permission management interface for superusers and managers
    """
    return render(request, 'admin/permission_management.html', {
        'title': 'Permission Management',
        'user': request.user
    })


@staff_or_perm('manage_files')
def file_cleanup_page(request):
    """
    File cleanup management interface for administrators and staff with file management permissions
    """
    return render(request, 'admin/file_cleanup.html', {
        'title': 'Excel Import File Cleanup',
        'user': request.user
    })


# Custom exception handler for better error responses
def custom_exception_handler(exc, context):
    """
    Custom exception handler for better error responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Add more detailed error information
        response.data['error_code'] = getattr(exc, 'code', 'unknown_error')
        response.data['timestamp'] = timezone.now().isoformat()

        # Log the error for debugging
        logger.error(f"API Error: {exc.__class__.__name__}: {str(exc)}", extra={
            'user': getattr(context.get('request'), 'user', None),
            'view': context.get('view', {}).get('__class__', {}).get('__name__'),
            'method': getattr(context.get('request'), 'method', None),
            'path': getattr(context.get('request'), 'path', None),
        })

    return response


# ============================================================================
# PHOTO MANAGEMENT UI VIEWS
# ============================================================================

@login_required
@staff_or_perm('view_task')
def photo_upload_view(request):
    """Photo upload interface for staff"""
    # Get tasks that the user can access
    if request.user.is_superuser:
        tasks = Task.objects.filter(is_deleted=False).select_related('property_ref')
    else:
        # Get tasks for properties the user has access to
        accessible_properties = Property.objects.filter(
            Q(ownerships__user=request.user) |
            Q(tasks__assigned_to=request.user)
        ).distinct()
        tasks = Task.objects.filter(
            property_ref__in=accessible_properties,
            is_deleted=False
        ).select_related('property_ref')
    
    # Get pre-selected task from URL parameter
    selected_task_id = request.GET.get('task')
    selected_task = None
    if selected_task_id:
        try:
            selected_task = Task.objects.get(id=selected_task_id, is_deleted=False)
            # Verify user has access to this task
            if not request.user.is_superuser:
                accessible_properties = Property.objects.filter(
                    Q(ownerships__user=request.user) |
                    Q(tasks__assigned_to=request.user)
                ).distinct()
                if selected_task.property_ref not in accessible_properties:
                    selected_task = None
        except Task.DoesNotExist:
            selected_task = None
    
    context = {
        'tasks': tasks,
        'selected_task': selected_task,
        'user': request.user,
    }
    return render(request, 'photo_upload.html', context)


@login_required
@staff_or_perm('view_task')
def photo_management_view(request):
    """Photo management dashboard for staff"""
    context = {
        'user': request.user,
    }
    return render(request, 'photo_management.html', context)


@login_required
@staff_or_perm('view_task')
def photo_comparison_view(request, task_id):
    """Before/after photo comparison view for a specific task"""
    task = get_object_or_404(Task, id=task_id, is_deleted=False)
    
    # Check if user has access to this task
    if not request.user.is_superuser:
        accessible_properties = Property.objects.filter(
            Q(propertyownership__user=request.user) | 
            Q(assigned_to=request.user)
        ).distinct()
        if task.property_ref not in accessible_properties:
            raise PermissionDenied("You don't have permission to view this task's photos.")
    
    context = {
        'task': task,
        'user': request.user,
    }
    return render(request, 'photo_comparison.html', context)