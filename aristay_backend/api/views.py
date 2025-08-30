from django.contrib.auth.models import User
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.db import models
from .services.notification_service import NotificationService
from .models import NotificationVerb
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

import json

from .filters import TaskFilter
from .system_metrics import get_system_metrics

from rest_framework import generics, permissions, viewsets, filters
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status

from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
)

from .models import Task, Property, TaskImage, Device, Notification, Booking, PropertyOwnership
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
from .permissions import IsOwnerOrAssignedOrReadOnly, IsOwner, IsManagerOrOwner
from .services.notification_service import NotificationService


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAssignedOrReadOnly]
   
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
        # naive implementation: create Notification rows for staff managers + owners
        from django.contrib.auth.models import User
        managers = User.objects.filter(is_superuser=True) | User.objects.filter(is_staff=True)
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
        new_status = request.POST.get('status') or request.data.get('status')
        valid = {s for s, _ in Task.STATUS_CHOICES}
        if new_status not in valid:
            return Response({'error': 'Invalid status'}, status=400)
        old = Task.objects.get(pk=task.pk)
        task.status = new_status
        task.modified_by = request.user
        task.save(update_fields=['status', 'modified_by', 'modified_at'])
        NotificationService.notify_on_update(old, task, actor=request.user)
        return Response({'status': new_status})


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related('property').all()
    serializer_class = BookingSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ['guest_name', 'guest_contact', 'property__name']
    ordering_fields = ['check_in_date', 'check_out_date', 'status']
    ordering = ['-check_in_date']


class PropertyOwnershipViewSet(viewsets.ModelViewSet):
    queryset = PropertyOwnership.objects.select_related('property', 'user').all()
    serializer_class = PropertyOwnershipSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsManagerOrOwner]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['property__name', 'user__username', 'user__email']

# ----------------------------------------------------------------------------
# Portal (web) views – property → bookings → tasks flow
# ----------------------------------------------------------------------------
from django.contrib.auth.decorators import login_required


@login_required
def portal_home(request):
    from django.shortcuts import render
    from django.db.models import Count
    
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
    except:
        # User has no profile, still get basic task counts
        assigned_tasks = Task.objects.filter(assigned_to=request.user)
        assigned_tasks_count = assigned_tasks.count()
        pending_tasks_count = assigned_tasks.filter(status='pending').count()
        pass
    
    # Get booking counts for accessible properties
    from .models import Booking
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


def _accessible_properties_for(user):
    """Return a queryset of properties visible to this user."""
    if user.is_superuser or user.is_staff:
        return Property.objects.all().order_by('name')
    # viewer/owner or crew: properties they own/view or have tasks on
    owned = Property.objects.filter(ownerships__user=user)
    assigned = Property.objects.filter(tasks__assigned_to=user)
    return (owned | assigned).distinct().order_by('name')


@login_required
def portal_property_list(request):
    from django.utils import timezone as djtz
    now = djtz.now()
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
    })


@login_required
def portal_property_detail(request, pk):
    from django.utils import timezone as djtz
    now = djtz.now()
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
        'search_q': q or '',
        'page': page,
        'has_next': end < total,
        'has_prev': start > 0,
    })


@login_required
def portal_task_detail(request, task_id):
    """User-friendly task detail view for portal users."""
    from django.shortcuts import get_object_or_404
    
    task = get_object_or_404(Task.objects.select_related('property', 'booking', 'assigned_to', 'created_by'), id=task_id)
    
    # Check permissions - users can view tasks they're assigned to, or if they're staff, or if they have access to the property
    accessible_properties = _accessible_properties_for(request.user)
    if not (request.user.is_staff or 
            task.assigned_to == request.user or 
            task.property in accessible_properties):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("You don't have permission to view this task.")
    
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
    except:
        pass
    
    # Check if user can edit (assigned to them or staff)
    can_edit = task.assigned_to == request.user or request.user.is_staff
    
    context = {
        'task': task,
        'checklist': checklist,
        'responses_by_room': responses_by_room,
        'can_edit': can_edit,
    }
    
    return render(request, 'portal/task_detail.html', context)


# DRF ViewSets and API Views start here
# ============================================================================

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'task_type', 'property', 'assigned_to']
    search_fields = ['title', 'description']
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAssignedOrReadOnly]

    def perform_update(self, serializer):
        old = Task.objects.get(pk=serializer.instance.pk)
        instance = serializer.save(modified_by=self.request.user)

        changes = []
        for field in ('status', 'title', 'description', 'assigned_to', 'task_type', 'property'):
            old_val = getattr(old, field)
            new_val = getattr(instance, field)
            if field == 'assigned_to':
                old_val = old.assigned_to.username if old.assigned_to else None
                new_val = instance.assigned_to.username if instance.assigned_to else None
            if field == 'property':
                old_val = old.property.name if old.property else None
                new_val = instance.property.name if instance.property else None

            if old_val != new_val:
                changes.append(
                    f"{timezone.now().isoformat()}: "
                    f"{self.request.user.username} changed {field} "
                    f"from '{old_val or ''}' to '{new_val or ''}'"
                )

        history = json.loads(old.history or '[]')
        history.extend(changes)
        Task.objects.filter(pk=instance.pk).update(history=json.dumps(history))

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unmute(self, request, pk=None):
        """
        POST /api/tasks/<id>/unmute/
        """
        task = self.get_object()
        task.muted_by.remove(request.user)
        return Response({'muted': False})
        


class TaskImageCreateView(generics.CreateAPIView):
    """
    POST /api/tasks/{task_pk}/images/
    """
    serializer_class = TaskImageSerializer
    parser_classes = [MultiPartParser, FormParser]
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrAssignedOrReadOnly]

    def perform_create(self, serializer):
        # 1) load the Task
        task = generics.get_object_or_404(Task, pk=self.kwargs['task_pk'])
        # 2) save the new TaskImage
        image = serializer.save(task=task)
        # history (kept as you have)
        history = json.loads(task.history or '[]')
        history.append(f"{timezone.now().isoformat()}: {self.request.user.username} added photo {image.image.url}")
        Task.objects.filter(pk=task.pk).update(history=json.dumps(history))
        # notify
        NotificationService.notify_task_photo(task, added=True, actor=self.request.user)


class TaskImageDetailView(generics.RetrieveDestroyAPIView):
    """
    GET, DELETE /api/tasks/{task_pk}/images/{pk}/
    """
    queryset = TaskImage.objects.all()
    serializer_class = TaskImageSerializer
    parser_classes = [MultiPartParser, FormParser]
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrAssignedOrReadOnly]

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


class TaskListCreate(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAssignedOrReadOnly]

    def perform_update(self, serializer):
        old = Task.objects.get(pk=serializer.instance.pk)
        instance = serializer.save(modified_by=self.request.user)

        changes = []
        for field in ('status', 'title', 'description', 'assigned_to', 'task_type', 'property'):
            old_val = getattr(old, field)
            new_val = getattr(instance, field)
            if field == 'assigned_to':
                old_val = old.assigned_to.username if old.assigned_to else None
                new_val = instance.assigned_to.username if instance.assigned_to else None
            if field == 'property':
                old_val = old.property.name if old.property else None
                new_val = instance.property.name if instance.property else None

            if old_val != new_val:
                changes.append(
                    f"{timezone.now().isoformat()}: "
                    f"{self.request.user.username} changed {field} "
                    f"from '{old_val or ''}' to '{new_val or ''}'"
                )

        history = json.loads(old.history or '[]')
        history.extend(changes)
        Task.objects.filter(pk=instance.pk).update(history=json.dumps(history))


class PropertyListCreate(generics.ListCreateAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None

    def get_permissions(self):
        # only admins can create
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return super().get_permissions()
    
class PropertyDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        # Only admins can modify/delete; reads remain open to authenticated (or read-only if you prefer)
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdminUser()]
        return super().get_permissions()

class UserList(generics.ListAPIView):
    queryset = User.objects.all().order_by('id')  # ← Add ordering to fix pagination warning
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields  = ['username', 'email']

class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    """
    GET/PATCH /api/admin/users/<id>/
    Owner-only for updates. Safe fields: is_active, is_staff.
    """
    queryset = User.objects.all()
    serializer_class = AdminUserAdminSerializer
    permission_classes = [IsOwner]  # superuser only

    # (Optional safety: forbid changing superusers except by self)
    def perform_update(self, serializer):
        target: User = self.get_object()
        actor: User  = self.request.user
        data = serializer.validated_data

        # never allow anyone to toggle a superuser other than themselves
        if target.is_superuser and target != actor:
            raise PermissionDenied("Cannot modify another owner account.")

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

class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    GET /api/users/me/
    """
    serializer_class       = UserSerializer
    authentication_classes = [TokenAuthentication]
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
        return (
            Notification.objects
            .filter(recipient=self.request.user)
            .order_by('-timestamp', '-id')  # newest first, stable
        )
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_notification_count(request):
    count = Notification.objects.filter(recipient=request.user, read=False).count()
    return Response({'unread': count})
    
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    count = Notification.objects.filter(recipient=request.user, read=False).update(
        read=True,
        read_at=timezone.now()
    )
    return Response({'success': True, 'marked_count': count})

# ---------- Manager dashboard: overview ----------
@api_view(['GET'])
@permission_classes([IsManagerOrOwner])
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

# ---------- Manager: list employees/managers (no owners) ----------
class ManagerUserList(generics.ListAPIView):
    serializer_class   = UserSerializer  # includes role (read-only)
    authentication_classes = [TokenAuthentication]
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
class ManagerUserDetail(generics.RetrieveUpdateAPIView):
    queryset = User.objects.filter(is_superuser=False)
    serializer_class = ManagerUserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsManagerOrOwner]

# ---------- NEW: Manager Charts Dashboard ----------
def _check_manager_permission(user):
    """Helper to check if user has manager permissions"""
    if not (user and user.is_authenticated and user.is_active):
        return False
    if user.is_superuser:
        return True
    role = getattr(getattr(user, 'profile', None), 'role', 'staff')
    return role == 'manager'

@staff_member_required
def manager_charts_dashboard(request):
    """
    Charts dashboard view for managers accessible at /manager/charts/
    Shows tasks by status, property, and task types with Chart.js visualizations
    """
    # Check manager permission
    if not _check_manager_permission(request.user):
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
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
        .select_related('property')
        .values('property__name')
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
    from datetime import timedelta
    thirty_days_ago = now - timedelta(days=30)
    daily_completions = (
        Task.objects
        .filter(status='completed', modified_at__gte=thirty_days_ago)
        .extra(select={'day': 'DATE(modified_at)'})
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
        property_name = item['property__name'] or 'No Property'
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

@staff_member_required
def admin_charts_dashboard(request):
    """
    Regular admin charts dashboard at /api/admin/charts/
    Shows same analytics but accessible to all Django admin users
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
        .select_related('property')
        .values('property__name')
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
    from datetime import timedelta
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
        property_name = item['property__name'] or 'No Property'
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


@staff_member_required
def system_metrics_dashboard(request):
    """
    System metrics and health dashboard for superusers
    Provides comprehensive system monitoring and performance insights
    """
    # Only allow superusers to access system metrics
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("System metrics are only available to superusers.")
    
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


@staff_member_required 
def system_metrics_api(request):
    """
    API endpoint for real-time system metrics (JSON)
    Used for dashboard auto-refresh
    """
    # Only allow superusers to access system metrics
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        metrics = get_system_metrics()
        return JsonResponse(metrics)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def system_logs_viewer(request):
    """
    Log file viewer for superusers to examine system logs
    Provides search, filtering, and real-time viewing capabilities
    """
    # Only allow superusers to access logs
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Log viewer is only available to superusers.")
    
    import os
    from django.conf import settings
    
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


@staff_member_required
def system_crash_recovery(request):
    """
    System crash recovery and diagnostic information
    Helps superusers understand and recover from system failures
    """
    # Only allow superusers
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Crash recovery is only available to superusers.")
    
    import os
    import subprocess
    from django.conf import settings
    
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

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .services.excel_import_service import ExcelImportService
from .models import BookingImportTemplate, Property

def is_superuser_or_manager(user):
    """Check if user is superuser or manager"""
    return user.is_superuser or (hasattr(user, 'profile') and user.profile.role in ['manager', 'superuser'])

@login_required
@user_passes_test(is_superuser_or_manager)
def excel_import_view(request):
    """View for importing Excel booking schedules"""
    
    if request.method == 'POST':
        try:
            excel_file = request.FILES.get('excel_file')
            if not excel_file:
                messages.error(request, 'Please select an Excel file to import.')
                return redirect('excel-import')
            
            # Check file extension
            if not excel_file.name.endswith(('.xlsx', '.xls')):
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
            
            # Process the Excel file
            import_service = ExcelImportService(request.user, template)
            result = import_service.import_excel_file(excel_file)
            
            if result['success']:
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
                
                if result.get('new_properties_created', 0) > 0:
                    messages.info(request, f"Created {result['new_properties_created']} new properties during import.")
                
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
            messages.error(request, f"Import failed: {str(e)}")
            import logging
            logging.error(f"Excel import error: {e}")
    
    # Get recent import logs
    recent_imports = []
    if hasattr(request.user, 'profile') and request.user.profile.role in ['manager', 'superuser']:
        from .models import BookingImportLog
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
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        # Process the Excel file
        import_service = ExcelImportService(request.user)
        result = import_service.import_excel_file(excel_file)
        
        # If properties need approval, return special response
        if result.get('requires_property_approval'):
            result['message'] = f"Import requires admin approval. Found {len(result.get('new_properties', []))} new properties."
        
        return JsonResponse(result)
        
    except Exception as e:
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