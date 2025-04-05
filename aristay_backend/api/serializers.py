from django.contrib.auth.models import User
from rest_framework import serializers
from .models import CleaningTask

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

class CleaningTaskSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = CleaningTask
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at')