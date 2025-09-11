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
from drf_spectacular.utils import extend_schema_field, inline_serializer
from drf_spectacular.types import OpenApiTypes

from rest_framework import serializers
from .models import Task, Property, TaskImage, Profile, Device, Notification, UserRole
from .models import Booking, PropertyOwnership, AuditEvent  # Agent's Phase 2: Add AuditEvent
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
    task_group   = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        # include email so we can show it, and is_staff for "Admin" flag
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_superuser', 'is_active',   # ← include is_superuser
            'role', 'task_group', 'timezone', 'system_timezone',
        ]
        
    @extend_schema_field(OpenApiTypes.STR)
    def get_role(self, obj):
        # Superusers override role; show "superuser" regardless of stored profile.role
        if obj.is_superuser:
            return 'superuser'
        try:
            return obj.profile.role
        except Profile.DoesNotExist:
            return 'staff'

    @extend_schema_field(OpenApiTypes.STR)
    def get_task_group(self, obj):
        try:
            return obj.profile.task_group
        except Profile.DoesNotExist:
            return 'none'

    @extend_schema_field(OpenApiTypes.STR)
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
    # Serializer for TaskImage with before/after photo functionality
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    photo_type_display = serializers.CharField(source='get_photo_type_display', read_only=True)
    photo_status_display = serializers.CharField(source='get_photo_status_display', read_only=True)
    
    class Meta:
        model = TaskImage
        fields = [
            'id', 'image', 'uploaded_at', 'uploaded_by', 'uploaded_by_username',
            'size_bytes', 'width', 'height', 'original_size_bytes',
            # NEW: Before/After photo fields
            'photo_type', 'photo_type_display', 'photo_status', 'photo_status_display',
            'sequence_number', 'is_primary', 'description'
        ]
        read_only_fields = ['uploaded_by', 'uploaded_by_username', 'size_bytes', 
                           'width', 'height', 'original_size_bytes', 'photo_type_display', 'photo_status_display']
    
    def validate_image(self, file):
        """Agent's enhanced validation: Accept large files, validate before optimization."""
        from django.conf import settings
        from rest_framework import serializers
        
        # Inline validation for security test compliance
        max_mb = getattr(settings, 'MAX_UPLOAD_BYTES', 25 * 1024 * 1024) // (1024 * 1024)
        if file.size > max_mb * 1024 * 1024:
            raise serializers.ValidationError(f"Image is too large (> {max_mb} MB). Please choose a smaller photo.")
        
        # Validate allowed content types
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if file.content_type not in allowed_types:
            raise serializers.ValidationError("Unsupported file type. Please upload JPEG, PNG, or WebP images.")
        
        return file
    
    def validate(self, data):
        """Validate before/after photo constraints"""
        from rest_framework import serializers
        
        # Validate sequence number is positive
        if 'sequence_number' in data and data['sequence_number'] <= 0:
            raise serializers.ValidationError("Sequence number must be positive.")
        
        # Validate primary photo constraint
        if data.get('is_primary', False) and 'photo_type' in data:
            # Note: task will be set in perform_create, so we skip this validation here
            # The constraint will be enforced at the model level
            pass
        
        return data
    
    def create(self, validated_data):
        """Agent's optimization approach: Transform large uploads before storage."""
        from api.utils.image_ops import optimize_image  # do NOT call get_image_metadata here
        from django.core.files.base import ContentFile
        from django.conf import settings
        
        file = validated_data['image']
        original_size = getattr(file, 'size', None)
        
        try:
            optimized_bytes, optimization_metadata = optimize_image(
                file,
                max_dimension=getattr(settings, 'STORED_IMAGE_MAX_DIM', 2048),
                target_size=getattr(settings, 'STORED_IMAGE_TARGET_BYTES', 5 * 1024 * 1024),
                use_webp=True
            )
            # keep a sane name; extension doesn't strictly matter for storage backends
            name = getattr(file, 'name', 'upload')
            optimized_file = ContentFile(optimized_bytes, name=f"opt_{name}")
        except ValueError:
            target_mb = getattr(settings, 'STORED_IMAGE_TARGET_BYTES', 5 * 1024 * 1024) // (1024 * 1024)
            raise serializers.ValidationError({
                "image": f"We couldn't optimize this photo under {target_mb}MB. Please crop or choose a smaller one."
            })

        validated_data['image'] = optimized_file
        # DO NOT call get_image_metadata() here; use optimization_metadata from optimize_image()
        validated_data.update({
            'size_bytes': optimization_metadata.get('size_bytes'),
            'width': optimization_metadata.get('width'), 
            'height': optimization_metadata.get('height'),
            'original_size_bytes': optimization_metadata.get('original_size_bytes', original_size)
        })

        return super().create(validated_data)

class TaskSerializer(serializers.ModelSerializer):
    property_name           = serializers.CharField(source='property.name',    read_only=True)
    booking_id              = serializers.IntegerField(source='booking.id', read_only=True)
    booking_window          = serializers.SerializerMethodField(read_only=True)
    property_ref            = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all())
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
          'property_ref',
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
        
    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_muted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.muted_by.filter(pk=request.user.pk).exists()
        return False
    
    @extend_schema_field(
        inline_serializer(
            name="BookingWindow",
            fields={
                "start": serializers.DateTimeField(allow_null=True),
                "end": serializers.DateTimeField(allow_null=True),
            },
        )
    )
    def get_booking_window(self, obj):
        """Return booking window as formatted string."""
        if obj.booking:
            try:
                start = timezone.localtime(obj.booking.check_in_date).date().isoformat()
                end = timezone.localtime(obj.booking.check_out_date).date().isoformat()
                return f"{start} → {end}"
            except Exception:
                return None
        return None
    
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



        return ret

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
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

    @extend_schema_field(OpenApiTypes.STR)
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


# =============================================================================
# AGENT'S PHASE 2: AUDIT SYSTEM SERIALIZERS
# =============================================================================

class AuditEventSerializer(serializers.ModelSerializer):
    """
    Agent's Phase 2: Serializer for audit events.
    Fixed per GPT agent: actor as PK for test compatibility.
    """
    actor = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "created_at",
            "action",
            "object_type",
            "object_id",
            "actor",
            "request_id",
            "ip_address",
            "user_agent",
            "changes",
        ]