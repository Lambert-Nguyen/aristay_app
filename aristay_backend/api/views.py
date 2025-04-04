from rest_framework import generics
from .models import CleaningTask
from .serializers import CleaningTaskSerializer

# Existing view for listing and creating tasks
class CleaningTaskListCreate(generics.ListCreateAPIView):
    queryset = CleaningTask.objects.all()
    serializer_class = CleaningTaskSerializer

# New view for retrieving, updating, and deleting a single task
class CleaningTaskDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CleaningTask.objects.all()
    serializer_class = CleaningTaskSerializer