from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Task, Property, TaskImage
import json
from django.utils import timezone

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ['id', 'name']

class TaskImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskImage
        fields = ['id', 'image', 'uploaded_at']

class TaskSerializer(serializers.ModelSerializer):
    property_name           = serializers.CharField(source='property.name',    read_only=True)
    property                = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all())
    created_by              = serializers.CharField(source='created_by.username',   read_only=True)
    assigned_to_username    = serializers.CharField(source='assigned_to.username',  read_only=True)
    modified_by_username    = serializers.CharField(source='modified_by.username',  read_only=True)
    images                  = TaskImageSerializer(many=True, read_only=True)


    # Replace ListField with a proper JSON parser:
    history                 = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
          'id',
          'property',
          'property_name',
          'task_type',
          'title',
          'description',
          'status',
          'created_by',
          'assigned_to',
          'assigned_to_username',
          'modified_by_username',
          'history',
          'created_at',
          'modified_at',
          'images',
        ]

    def get_history(self, obj):
        """
        obj.history is a JSON‐encoded string; decode it to a Python list.
        """
        try:
            return json.loads(obj.history or '[]')
        except json.JSONDecodeError:
            return []

    def _append_history(self, instance, user, changes):
        existing = self.get_history(instance)
        timestamp = timezone.now().isoformat()
        for change in changes:
            existing.append(f"{timestamp}: {user.username} {change}")
        return json.dumps(existing)

    def create(self, validated_data):
        user = self.context['request'].user
        # initial history entry
        validated_data['history']     = json.dumps([f"{timezone.now().isoformat()}: {user.username} created task"])
        validated_data['created_by']  = user
        validated_data['modified_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        changes = []
        for field in ('status', 'title', 'description', 'assigned_to', 'task_type', 'property'):
            if field in validated_data:
                old = getattr(instance, field)
                new = validated_data[field]
                old_val = getattr(old, 'id', old)
                new_val = getattr(new, 'id', new)
                if old_val != new_val:
                    changes.append(f"changed {field} from '{old_val}' to '{new_val}'")
        if changes:
            validated_data['history']     = self._append_history(instance, user, changes)
            validated_data['modified_by'] = user
        return super().update(instance, validated_data)