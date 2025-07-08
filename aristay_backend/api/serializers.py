from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Task, Property
import json

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

class TaskSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to = serializers.CharField(source='assigned_to.username', read_only=True, default='Not assigned')
    # Use a JSONField for history (or parse the JSON stored in a TextField)
    history = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'history')

    def get_history(self, obj):
        try:
            return json.loads(obj.history)
        except (ValueError, TypeError):
            return []
        
class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ['id', 'name', 'address', 'created_at', 'created_by', 'modified_at', 'modified_by']