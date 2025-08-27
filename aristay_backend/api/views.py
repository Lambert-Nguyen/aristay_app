from django.contrib.auth.models import User
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from .services.notification_service import NotificationService
from .models import NotificationVerb

import json

from .filters import TaskFilter

from rest_framework import generics, permissions, viewsets, filters
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status

from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
)

from .models import Task, Property, TaskImage, Device, Notification
from .serializers import (
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
)
from .permissions import IsOwnerOrAssignedOrReadOnly, IsOwner
from .services.notification_service import NotificationService


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
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