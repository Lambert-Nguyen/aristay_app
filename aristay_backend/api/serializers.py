from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Task, Property

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


class TaskSerializer(serializers.ModelSerializer):
    # read‐only nested name of the property
    property_name       = serializers.CharField(source='property.name',      read_only=True)
    # raw PK for writes
    property            = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all())
    # read‐only usernames
    created_by          = serializers.CharField(source='created_by.username',      read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username',     read_only=True)
    modified_by         = serializers.CharField(source='modified_by.username',     read_only=True)
    history             = serializers.ListField(read_only=True)  # assuming JSONField

    class Meta:
        model = Task
        fields = [
            'id',
            'property',            # for writes
            'property_name',       # for reads
            'task_type',
            'title',
            'description',
            'status',
            'created_by',
            'assigned_to',         # raw PK if you need it
            'assigned_to_username',# NEW read‐only username
            'modified_by',
            'history',
            'created_at',
            'modified_at',
        ]