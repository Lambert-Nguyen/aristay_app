from rest_framework import serializers
from .models import CleaningTask

class CleaningTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = CleaningTask
        fields = '__all__'