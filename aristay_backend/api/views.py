from django.contrib.auth.models import User
from django.utils import timezone
import json

from rest_framework import generics, permissions, viewsets
from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.permissions import AllowAny  # Import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAdminUser


from .models import Task, Property, TaskImage


from .serializers import TaskSerializer
from .serializers import PropertySerializer
from .serializers import UserSerializer
from .serializers import UserRegistrationSerializer
from .serializers import TaskImageSerializer


from .permissions import IsOwnerOrAssignedOrReadOnly  # Import our custom permission

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAssignedOrReadOnly]

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
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssignedOrReadOnly]

    def perform_create(self, serializer):
        task = generics.get_object_or_404(Task, pk=self.kwargs['task_pk'])
        image = serializer.save(task=task)
        # --- append history entry on Task ----
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
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssignedOrReadOnly]

    def perform_destroy(self, instance):
        task = instance.task
        timestamp = timezone.now().isoformat()
        user = self.request.user.username
        url = instance.image.url
        # first delete the file record
        instance.delete()
        # then append to task.history
        history = json.loads(task.history or '[]')
        history.append(f"{timestamp}: {user} deleted photo {url}")
        Task.objects.filter(pk=task.pk).update(history=json.dumps(history))

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]  # Allow any user (authenticated or not)

class TaskListCreate(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # Set the current user as the task's creator
        serializer.save(created_by=self.request.user)

class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAssignedOrReadOnly]

    def perform_update(self, serializer):
        # 1) load the old instance
        old = Task.objects.get(pk=serializer.instance.pk)

        # 2) do the actual update, stamping modified_by
        instance = serializer.save(modified_by=self.request.user)

        # 3) build a list of change‐entries
        changes = []
        for field in ('status', 'title', 'description', 'assigned_to', 'task_type', 'property'):
            old_val = getattr(old, field)
            new_val = getattr(instance, field)
            # if assigned_to or property you'll want .username or .name
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

        # 4) append to the JSONField (you’re using a TextField with JSON in it)
        history = json.loads(old.history or '[]')
        history.extend(changes)
        instance.history = json.dumps(history)
        # 5) save only the history column to avoid looping back into perform_update
        Task.objects.filter(pk=instance.pk).update(history=instance.history)

class PropertyListCreate(generics.ListCreateAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = None
        
class UserList(generics.ListAPIView):
    """
    GET /api/users/
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]