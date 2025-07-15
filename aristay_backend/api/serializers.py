from django.contrib.auth.models import User
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator

from django.core.mail import send_mail

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from django.conf import settings

from rest_framework import serializers
from .models import Task, Property, TaskImage
import json
from django.utils import timezone

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # include email so we can show it, and is_staff for “Admin” flag
        fields = ['id', 'username', 'email', 'is_staff']
        
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
    images = TaskImageSerializer(many=True, read_only=True)


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
    
class AdminInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField()

    def validate_username(self, username):
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("Username already taken")
        return username

    def create(self, validated_data):
        # 1) generate a random password via your User manager
        random_pw = BaseUserManager().make_random_password()
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=random_pw,
        )
        user.is_active = False  # force them to set password
        user.save()

        # 2) build a one-time activation link
        token = default_token_generator.make_token(user)
        uid  = urlsafe_base64_encode(force_bytes(user.pk))
        link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"

        # 3) email them
        send_mail(
            subject="You’ve been invited!",
            message=f"Click here to activate your account:\n\n{link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        return user

class AdminPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def create(self, validated_data):
        # reuse Django’s password-reset form
        from django.contrib.auth.forms import PasswordResetForm
        form = PasswordResetForm(data=validated_data)
        if form.is_valid():
            form.save(
                email_template_name="registration/password_reset_email.html",
                request=self.context['request']
            )
            return validated_data
        else:
            raise serializers.ValidationError(form.errors)
        
class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    is_staff = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = ('username','email','password','is_staff')
    
    
    def validate_password(self, pw):
        # raise a ValidationError if pw too weak
        validate_password(pw)
        return pw


    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        user.is_staff = validated_data.get('is_staff', False)
        user.save()
        return user