from django.contrib.auth.models import User
from django.utils import timezone
import json

from rest_framework import generics, permissions, viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
)

from .models import Task, Property, TaskImage
from .serializers import (
    TaskSerializer,
    PropertySerializer,
    UserSerializer,
    UserRegistrationSerializer,
    TaskImageSerializer,
    AdminInviteSerializer,
    AdminPasswordResetSerializer,
    AdminUserCreateSerializer,
)
from .permissions import IsOwnerOrAssignedOrReadOnly


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAssignedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, modified_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)


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
        # 3) append an "added photo" entry to task.history
        history = json.loads(task.history or '[]')
        timestamp = timezone.now().isoformat()
        user = self.request.user.username
        url = image.image.url
        history.append(f"{timestamp}: {user} added photo {url}")
        Task.objects.filter(pk=task.pk).update(history=json.dumps(history))


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
        timestamp = timezone.now().isoformat()
        user = self.request.user.username
        url = instance.image.url
        # 2) delete the TaskImage record (and its file)
        instance.delete()
        # 3) append a "deleted photo" entry to task.history
        history = json.loads(task.history or '[]')
        history.append(f"{timestamp}: {user} deleted photo {url}")
        Task.objects.filter(pk=task.pk).update(history=json.dumps(history))


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

class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


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

class CurrentUserView(generics.RetrieveAPIView):
    """
    GET /api/users/me/
    """
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    
class AdminUserCreateView(generics.CreateAPIView):
    """
    POST /api/admin/create-user/
    """
    permission_classes = [IsAdminUser]
    serializer_class   = AdminUserCreateSerializer