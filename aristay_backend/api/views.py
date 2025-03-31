from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from .models import CleaningTask
from .serializers import CleaningTaskSerializer

class CleaningTaskListCreate(generics.ListCreateAPIView):
    queryset = CleaningTask.objects.all()
    serializer_class = CleaningTaskSerializer