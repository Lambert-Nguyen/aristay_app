"""
Test suite for critical security fixes in models.

This test verifies the security fixes implemented based on the GPT agent's recommendations:
1. Fix duplicate signal receivers
2. Update TaskImage.uploaded_by to use AUTH_USER_MODEL
3. Fix time_of_day string default
4. Secure file upload with UUID naming and validation
"""

import os
import tempfile
from datetime import time
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from PIL import Image
import io

from api.models import Profile, TaskImage, Task, Property
from api.mixins import SoftDeleteMixin, TimeStampedMixin, UserStampedMixin, SourceStampedMixin

User = get_user_model()


class SecurityFixesTestCase(TestCase):
    """Test critical security fixes."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.property = Property.objects.create(
            name='Test Property',
            address='123 Test St',
            created_by=self.user,
            modified_by=self.user
        )

    def test_single_signal_receiver_creates_profile(self):
        """Test that profile is created without duplicate signals."""
        # Create a new user
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )
        
        # Verify profile was created
        self.assertTrue(Profile.objects.filter(user=new_user).exists())
        
        # Verify only one profile exists
        profile_count = Profile.objects.filter(user=new_user).count()
        self.assertEqual(profile_count, 1)

    def test_taskimage_uses_auth_user_model(self):
        """Test that TaskImage.uploaded_by uses AUTH_USER_MODEL."""
        from django.conf import settings
        
        # Create a task
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            property=self.property,
            created_by=self.user,
            modified_by=self.user
        )
        
        # Create task image
        image = self.create_test_image()
        task_image = TaskImage.objects.create(
            task=task,
            image=image,
            uploaded_by=self.user
        )
        
        # Verify uploaded_by field uses correct model
        uploaded_by_field = TaskImage._meta.get_field('uploaded_by')
        self.assertEqual(uploaded_by_field.related_model, User)
        self.assertEqual(uploaded_by_field.related_model._meta.label, settings.AUTH_USER_MODEL)

    def test_time_of_day_uses_time_object(self):
        """Test that time_of_day field uses time object, not string."""
        from api.models import ScheduleTemplate
        
        # Get the default value for time_of_day
        time_of_day_field = ScheduleTemplate._meta.get_field('time_of_day')
        default_value = time_of_day_field.default
        
        # Should be a time object, not string
        self.assertIsInstance(default_value, time)
        self.assertEqual(default_value, time(9, 0))

    def test_secure_file_upload_path(self):
        """Test that file upload uses UUID naming."""
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            property=self.property,
            created_by=self.user,
            modified_by=self.user
        )
        
        # Create task image
        image = self.create_test_image()
        task_image = TaskImage.objects.create(
            task=task,
            image=image,
            uploaded_by=self.user
        )
        
        # Verify path structure
        image_path = task_image.image.name
        self.assertTrue(image_path.startswith(f'task_images/{task.id}/'))
        
        # Verify UUID naming (32 hex chars + extension)
        filename = os.path.basename(image_path)
        name_part, ext = os.path.splitext(filename)
        self.assertEqual(len(name_part), 32)  # UUID hex string
        self.assertTrue(all(c in '0123456789abcdef' for c in name_part))
        self.assertEqual(ext, '.png')

    def test_file_size_validation(self):
        """Test that large files are rejected."""
        from api.models import validate_task_image
        
        # Create a mock large file
        large_file = SimpleUploadedFile(
            name='large.png',
            content=b'x' * (6 * 1024 * 1024),  # 6MB file
            content_type='image/png'
        )
        large_file.size = 6 * 1024 * 1024
        
        # Should raise validation error
        with self.assertRaises(ValidationError) as cm:
            validate_task_image(large_file)
        
        self.assertIn('too large', str(cm.exception))
        self.assertIn('5MB', str(cm.exception))

    def test_file_type_validation(self):
        """Test that invalid file types are rejected."""
        from api.models import validate_task_image
        
        # Create a mock file with invalid content type
        invalid_file = SimpleUploadedFile(
            name='test.exe',
            content=b'fake executable',
            content_type='application/x-executable'
        )
        invalid_file.size = 1000
        
        # Should raise validation error
        with self.assertRaises(ValidationError) as cm:
            validate_task_image(invalid_file)
        
        self.assertIn('Invalid image type', str(cm.exception))

    def create_test_image(self):
        """Create a test image file for upload testing."""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name='test.png',
            content=img_io.getvalue(),
            content_type='image/png'
        )


class MixinsTestCase(TestCase):
    """Test the new mixins functionality."""

    def test_timestamp_mixin(self):
        """Test TimeStampedMixin adds created_at and modified_at."""
        # Create test model using mixin
        class TestModel(TimeStampedMixin):
            pass
        
        # Check fields exist
        fields = [f.name for f in TestModel._meta.fields]
        self.assertIn('created_at', fields)
        self.assertIn('modified_at', fields)

    def test_user_stamped_mixin(self):
        """Test UserStampedMixin adds user tracking fields."""
        # Create test model using mixin
        class TestModel(UserStampedMixin):
            pass
        
        # Check fields exist
        fields = [f.name for f in TestModel._meta.fields]
        self.assertIn('created_by', fields)
        self.assertIn('modified_by', fields)

    def test_source_stamped_mixin(self):
        """Test SourceStampedMixin adds source tracking fields."""
        # Create test model using mixin
        class TestModel(SourceStampedMixin):
            pass
        
        # Check fields exist
        fields = [f.name for f in TestModel._meta.fields]
        self.assertIn('created_via', fields)
        self.assertIn('modified_via', fields)
        
        # Check choices
        created_via_field = TestModel._meta.get_field('created_via')
        choices = [choice[0] for choice in created_via_field.choices]
        self.assertIn('manual', choices)
        self.assertIn('excel_import', choices)
        self.assertIn('api', choices)
        self.assertIn('system', choices)

    def test_soft_delete_mixin(self):
        """Test SoftDeleteMixin adds soft delete functionality."""
        # Create test model using mixin
        class TestModel(SoftDeleteMixin):
            pass
        
        # Check fields exist
        fields = [f.name for f in TestModel._meta.fields]
        self.assertIn('is_deleted', fields)
        self.assertIn('deleted_at', fields)
        self.assertIn('deleted_by', fields)
        self.assertIn('deletion_reason', fields)


class SecurityComplianceTestCase(TestCase):
    """Test security compliance features."""

    def test_no_pii_in_audit_logs(self):
        """Test that PII is not stored in audit logs."""
        # This is a placeholder for future audit system testing
        # When AuditEvent model is implemented, test that sensitive fields
        # like guest_contact are redacted or hashed in audit logs
        pass

    def test_file_upload_security(self):
        """Test comprehensive file upload security."""
        task = Task.objects.create(
            title='Test Task',
            property=Property.objects.create(name='Test Property'),
            created_by=User.objects.create_user('testuser', 'test@example.com')
        )
        
        # Test valid image
        valid_image = self.create_test_image()
        task_image = TaskImage(task=task, image=valid_image)
        
        # Should not raise exception
        try:
            task_image.full_clean()
        except ValidationError:
            self.fail("Valid image should not raise ValidationError")

    def create_test_image(self):
        """Create a test image for security testing."""
        img = Image.new('RGB', (50, 50), color='blue')
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name='security_test.png',
            content=img_io.getvalue(),
            content_type='image/png'
        )
