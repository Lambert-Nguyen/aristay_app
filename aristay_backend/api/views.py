from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import CleaningTask
from .serializers import CleaningTaskSerializer

class CleaningTaskListCreate(generics.ListCreateAPIView):
    queryset = CleaningTask.objects.all()
    serializer_class = CleaningTaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

class CleaningTaskDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CleaningTask.objects.all()
    serializer_class = CleaningTaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]