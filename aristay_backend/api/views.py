from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.permissions import AllowAny  # Import AllowAny
from django.contrib.auth.models import User
from .serializers import UserRegistrationSerializer
from .models import CleaningTask
from .serializers import CleaningTaskSerializer
from .permissions import IsOwnerOrReadOnly  # Import our custom permission


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]  # Allow any user (authenticated or not)

class CleaningTaskListCreate(generics.ListCreateAPIView):
    queryset = CleaningTask.objects.all()
    serializer_class = CleaningTaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # Set the current user as the task's creator
        serializer.save(created_by=self.request.user)

class CleaningTaskDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CleaningTask.objects.all()
    serializer_class = CleaningTaskSerializer
    authentication_classes = [TokenAuthentication]
    # Combine default read-only permission with our owner check:
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]