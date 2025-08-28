from django.contrib.auth.models import User
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator

from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.dateparse import parse_datetime
from django.utils import timezone


from django.conf import settings

from rest_framework import serializers
from .models import Task, Property, TaskImage, Profile, Device, Notification, UserRole
from .models import Booking, PropertyOwnership
import json
import pytz

from zoneinfo import ZoneInfo
from datetime import datetime

class UserSerializer(serializers.ModelSerializer):
    timezone = serializers.CharField(source='profile.timezone')
    system_timezone = serializers.SerializerMethodField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)  # show disabled state
    is_superuser = serializers.BooleanField(read_only=True)
    role         = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        # include email so we can show it, and is_staff for “Admin” flag
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_superuser', 'is_active',   # ← include is_superuser
            'role', 'timezone', 'system_timezone',
        ]
        
    def get_role(self, obj):
        # Superusers override role; show “superuser” regardless of stored profile.role
        if obj.is_superuser:
            return 'superuser'
        try:
            return obj.profile.role
        except Profile.DoesNotExist:
            return 'staff'

    def get_system_timezone(self, obj):
        return settings.TIME_ZONE

    def update(self, instance, validated_data):
        # 1) pull off any profile-specific data
        profile_data = validated_data.pop('profile', {})
        tz = profile_data.get('timezone', None)

        # 2) if they sent a new timezone, write it on the Profile
        if tz is not None:
            profile = getattr(instance, 'profile', None) or Profile.objects.create(user=instance)
            profile.timezone = tz
            profile.save()

        # 3) update the rest of the User fields (email, etc.)
        return super().update(instance, validated_data)

# Admin can PATCH is_staff / is_active
class AdminUserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ('id','username','email','first_name','last_name','is_staff','is_active')

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class ManagerUserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', read_only=True)

    class Meta:
        model  = User
        fields = ('id','username','email','first_name','last_name','is_active','role')

    def update(self, instance, validated_data):
        # Managers may ONLY toggle is_active on Employees (role=staff), never owners.
        if instance.is_superuser:
            raise serializers.ValidationError("Cannot modify owner accounts.")
        role = getattr(getattr(instance, 'profile', None), 'role', 'staff')
        if role != 'staff':
            raise serializers.ValidationError("Managers can only modify Employees.")
        if 'is_active' in validated_data:
            instance.is_active = validated_data['is_active']
            instance.save(update_fields=['is_active'])
        return instance


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
    booking_id              = serializers.IntegerField(source='booking.id', read_only=True)
    booking_window          = serializers.SerializerMethodField(read_only=True)
    property                = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all())
    created_by              = serializers.CharField(source='created_by.username',   read_only=True)
    assigned_to_username    = serializers.CharField(source='assigned_to.username',  read_only=True)
    modified_by_username    = serializers.CharField(source='modified_by.username',  read_only=True)
    images = TaskImageSerializer(many=True, read_only=True)
    
    # NEW: “is_muted” for **current** user (read-only)
    is_muted = serializers.SerializerMethodField(read_only=True)

    # Replace ListField with a proper JSON parser:
    history                 = serializers.SerializerMethodField()
    
    due_date = serializers.DateTimeField(
        allow_null=True,
        required=False,
        format=None,           # default: ISO-8601 with timezone
        input_formats=None,    # accept ISO strings
    )

    # Dependencies
    depends_on = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all(), many=True, required=False)

    class Meta:
        model = Task
        fields = [
          'id',
          'property',
          'property_name',
          'booking',
          'booking_id',
          'booking_window',
          'task_type',
          'title',
          'description',
          'status',
          'created_by',
          'assigned_to',
          'assigned_to_username',
          'modified_by_username',
          'created_at',
          'modified_at',
          'due_date',
          'images',
          'history',
          'is_muted',
          'depends_on',
        ]
        
    def get_is_muted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.muted_by.filter(pk=request.user.pk).exists()
        return False
    
    # ------------ New validator ------------
    def validate_due_date(self, value):
        """
        Disallow setting a due_date in the past.
        """
        if value is not None and value < timezone.now():
            raise serializers.ValidationError("Due date cannot be in the past.")
        return value
    # ---------------------------------------

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        # pick the user’s TZ (falling back if no profile)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                user_tz = request.user.profile.timezone
            except ObjectDoesNotExist:
                # fallback if no Profile exists
                user_tz = settings.TIME_ZONE
        else:
            user_tz = settings.TIME_ZONE

        raw = ret.get('due_date')
        if raw:
            # 1) normalize to a datetime
            if isinstance(raw, str):
                # parse the ISO string
                dt = parse_datetime(raw)
            elif isinstance(raw, datetime):
                dt = raw
            else:
                dt = None

            if dt:
                # ensure it's timezone‐aware (DRF might give naive)
                if dt.tzinfo is None:
                    dt = timezone.make_aware(dt, timezone.utc)

                # 2) convert to the user’s timezone
                local_dt = timezone.localtime(dt, pytz.timezone(user_tz))

                # 3) write it back as ISO
                ret['due_date'] = local_dt.isoformat()

        # booking window display
        booking = getattr(instance, 'booking', None)
        if booking:
            try:
                start = timezone.localtime(booking.check_in_date).date().isoformat()
                end   = timezone.localtime(booking.check_out_date).date().isoformat()
                ret['booking_window'] = f"{start} → {end}"
            except Exception:
                ret['booking_window'] = None
        else:
            ret['booking_window'] = None

        return ret

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
        for field in ('status', 'title', 'description', 'assigned_to', 'task_type', 'property', 'due_date'):
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
        fields = ('id', 'username', 'email', 'password', 'is_staff')    
    
    def validate_password(self, pw):
        # raise a ValidationError if pw too weak
        validate_password(pw)
        return pw


    def create(self, validated_data):
        is_staff = validated_data.get('is_staff', False)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        user.is_staff = is_staff
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        if user.is_superuser:
            # leave profile.role as-is; serializer will report “owner”
            pass
        else:
            profile.role = UserRole.MANAGER if is_staff else UserRole.STAFF
            profile.save(update_fields=['role'])
        return user
    
class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'token']

class NotificationSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    verb_label = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id','task','task_title','verb','verb_label','read','read_at','timestamp']

    def get_verb_label(self, obj):
        return obj.get_verb_display()


class BookingSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    tasks_count = serializers.IntegerField(source='tasks.count', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'property', 'property_name', 'check_in_date', 'check_out_date',
            'guest_name', 'guest_contact', 'status', 'created_at', 'modified_at',
            'tasks_count'
        ]
        read_only_fields = ['created_at', 'modified_at', 'tasks_count']


class PropertyOwnershipSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = PropertyOwnership
        fields = [
            'id', 'property', 'property_name', 'user', 'username', 'email',
            'ownership_type', 'can_edit', 'created_at'
        ]
        read_only_fields = ['created_at']