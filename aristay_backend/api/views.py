from django.contrib.auth.models import User
from django.utils import timezone
import json

from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.permissions import AllowAny  # Import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAdminUser


from .models import Task
from .models import Property

from .serializers import TaskSerializer
from .serializers import PropertySerializer
from .serializers import UserSerializer
from .serializers import UserRegistrationSerializer


from .permissions import IsOwnerOrAssignedOrReadOnly  # Import our custom permission

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
    permission_classes = [IsAdminUser]
        
class UserList(generics.ListAPIView):
    """
    Lists all users (id + username), so the front end can
    populate its assignee dropdown.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]