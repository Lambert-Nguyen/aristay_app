"""
Final test suite for before/after photo functionality in TaskImage model.

This test suite validates the enhanced TaskImage model with before/after photo
categorization, approval workflow, and photo management features.
"""

import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from api.models import Property, Booking, Task, TaskImage
from api.serializers import TaskImageSerializer
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@pytest.fixture
def test_user():
    """Create a test user for photo uploads."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_property():
    """Create a test property."""
    return Property.objects.create(
        name='Test Property',
        address='123 Test St'
    )


@pytest.fixture
def test_booking(test_property):
    """Create a test booking."""
    check_in = timezone.now() + timedelta(days=1)
    check_out = check_in + timedelta(days=3)
    return Booking.objects.create(
        property=test_property,
        check_in_date=check_in,
        check_out_date=check_out,
        guest_name='Test Guest',
        status='confirmed'
    )


@pytest.fixture
def test_task(test_property, test_booking, test_user):
    """Create a test task."""
    return Task.objects.create(
        title='Test Cleaning Task',
        description='Clean the property',
        task_type='cleaning',
        property_ref=test_property,
        booking=test_booking,
        created_by=test_user,
        assigned_to=test_user
    )


class TestTaskImageModelEnhancements:
    """Test TaskImage model enhancements for before/after photos."""

    @pytest.mark.django_db
    def test_photo_type_choices(self):
        """Test that photo type choices are properly defined."""
        choices = TaskImage.PHOTO_TYPE_CHOICES
        expected_choices = [
            ('before', 'Before'),
            ('after', 'After'),
            ('during', 'During'),
            ('reference', 'Reference'),
            ('damage', 'Damage'),
            ('general', 'General'),
        ]
        assert choices == expected_choices

    @pytest.mark.django_db
    def test_photo_status_choices(self):
        """Test that photo status choices are properly defined."""
        choices = TaskImage.PHOTO_STATUS_CHOICES
        expected_choices = [
            ('pending', 'Pending Review'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('archived', 'Archived'),
        ]
        assert choices == expected_choices

    @pytest.mark.django_db
    def test_model_fields_exist(self, test_task, test_user):
        """Test that all new fields exist and have correct defaults."""
        # Create a TaskImage without image field to test other fields
        photo = TaskImage(
            task=test_task,
            uploaded_by=test_user,
            photo_type='before',
            description='Test description',
            sequence_number=1
        )
        
        # Test field values
        assert photo.photo_type == 'before'
        assert photo.photo_status == 'pending'  # Default
        assert photo.sequence_number == 1
        assert photo.is_primary is False  # Default
        assert photo.description == 'Test description'

    @pytest.mark.django_db
    def test_auto_primary_photo_assignment_logic(self, test_task, test_user):
        """Test the logic for auto-assigning primary photos."""
        # Test that first photo of a type becomes primary
        photo1 = TaskImage(
            task=test_task,
            uploaded_by=test_user,
            photo_type='before',
            sequence_number=1
        )
        photo1.save()
        assert photo1.is_primary is True

        # Test that second photo of same type is not primary
        photo2 = TaskImage(
            task=test_task,
            uploaded_by=test_user,
            photo_type='before',
            sequence_number=2
        )
        photo2.save()
        assert photo2.is_primary is False

        # Test that first photo of different type becomes primary
        photo3 = TaskImage(
            task=test_task,
            uploaded_by=test_user,
            photo_type='after',
            sequence_number=1
        )
        photo3.save()
        assert photo3.is_primary is True

    @pytest.mark.django_db
    def test_string_representation(self, test_task, test_user):
        """Test string representation includes photo type and sequence."""
        photo = TaskImage(
            task=test_task,
            uploaded_by=test_user,
            photo_type='before',
            sequence_number=1
        )
        photo.save()
        
        expected = f"Before image for {test_task.title} (#1)"
        assert str(photo) == expected

    @pytest.mark.django_db
    def test_photo_workflow_states(self, test_task, test_user):
        """Test photo approval workflow states."""
        # Create photo in pending state
        photo = TaskImage.objects.create(
            task=test_task,
            uploaded_by=test_user,
            photo_type='before',
            photo_status='pending',
            sequence_number=1
        )
        assert photo.photo_status == 'pending'

        # Update to approved
        photo.photo_status = 'approved'
        photo.save()
        assert photo.photo_status == 'approved'

        # Update to rejected
        photo.photo_status = 'rejected'
        photo.save()
        assert photo.photo_status == 'rejected'

        # Update to archived
        photo.photo_status = 'archived'
        photo.save()
        assert photo.photo_status == 'archived'


class TestBeforeAfterPhotoQueries:
    """Test query patterns for before/after photo functionality."""

    @pytest.mark.django_db
    def test_get_photos_by_type(self, test_task, test_user):
        """Test getting photos filtered by type."""
        # Create before and after photos
        before_photo = TaskImage.objects.create(
            task=test_task,
            uploaded_by=test_user,
            photo_type='before',
            sequence_number=1
        )
        after_photo = TaskImage.objects.create(
            task=test_task,
            uploaded_by=test_user,
            photo_type='after',
            sequence_number=1
        )

        # Get before photos
        before_photos = TaskImage.objects.filter(
            task=test_task,
            photo_type='before'
        )
        assert before_photos.count() == 1
        assert before_photos.first() == before_photo

        # Get after photos
        after_photos = TaskImage.objects.filter(
            task=test_task,
            photo_type='after'
        )
        assert after_photos.count() == 1
        assert after_photos.first() == after_photo

    @pytest.mark.django_db
    def test_get_primary_photos(self, test_task, test_user):
        """Test getting primary photos for a task."""
        # Create multiple photos of same type
        TaskImage.objects.create(
            task=test_task,
            uploaded_by=test_user,
            photo_type='before',
            sequence_number=1,
            is_primary=True
        )
        TaskImage.objects.create(
            task=test_task,
            uploaded_by=test_user,
            photo_type='before',
            sequence_number=2,
            is_primary=False
        )
        TaskImage.objects.create(
            task=test_task,
            uploaded_by=test_user,
            photo_type='after',
            sequence_number=1,
            is_primary=True
        )

        # Get all primary photos
        primary_photos = TaskImage.objects.filter(
            task=test_task,
            is_primary=True
        )
        assert primary_photos.count() == 2

        # Get primary before photos
        primary_before = TaskImage.objects.filter(
            task=test_task,
            photo_type='before',
            is_primary=True
        )
        assert primary_before.count() == 1

    @pytest.mark.django_db
    def test_get_photos_by_status(self, test_task, test_user):
        """Test getting photos filtered by approval status."""
        # Create photos with different statuses
        TaskImage.objects.create(
            task=test_task,
            uploaded_by=test_user,
            photo_type='before',
            photo_status='pending',
            sequence_number=1
        )
        TaskImage.objects.create(
            task=test_task,
            uploaded_by=test_user,
            photo_type='after',
            photo_status='approved',
            sequence_number=1
        )

        # Get pending photos
        pending_photos = TaskImage.objects.filter(
            task=test_task,
            photo_status='pending'
        )
        assert pending_photos.count() == 1

        # Get approved photos
        approved_photos = TaskImage.objects.filter(
            task=test_task,
            photo_status='approved'
        )
        assert approved_photos.count() == 1

    @pytest.mark.django_db
    def test_get_photos_for_booking(self, test_property, test_booking, test_user):
        """Test getting all photos for a booking via task relationship."""
        # Create tasks for the booking
        task1 = Task.objects.create(
            title='Cleaning Task',
            task_type='cleaning',
            property_ref=test_property,
            booking=test_booking,
            created_by=test_user
        )
        task2 = Task.objects.create(
            title='Maintenance Task',
            task_type='maintenance',
            property_ref=test_property,
            booking=test_booking,
            created_by=test_user
        )

        # Create photos for both tasks
        TaskImage.objects.create(
            task=task1,
            uploaded_by=test_user,
            photo_type='before',
            sequence_number=1
        )
        TaskImage.objects.create(
            task=task1,
            uploaded_by=test_user,
            photo_type='after',
            sequence_number=1
        )
        TaskImage.objects.create(
            task=task2,
            uploaded_by=test_user,
            photo_type='before',
            sequence_number=1
        )

        # Get all photos for the booking
        booking_photos = TaskImage.objects.filter(task__booking=test_booking)
        assert booking_photos.count() == 3

        # Get before photos for the booking
        before_photos = TaskImage.objects.filter(
            task__booking=test_booking,
            photo_type='before'
        )
        assert before_photos.count() == 2

        # Get after photos for the booking
        after_photos = TaskImage.objects.filter(
            task__booking=test_booking,
            photo_type='after'
        )
        assert after_photos.count() == 1

    @pytest.mark.django_db
    def test_get_photos_by_task_type(self, test_property, test_booking, test_user):
        """Test getting photos filtered by task type."""
        # Create different task types
        cleaning_task = Task.objects.create(
            title='Cleaning Task',
            task_type='cleaning',
            property_ref=test_property,
            booking=test_booking,
            created_by=test_user
        )
        maintenance_task = Task.objects.create(
            title='Maintenance Task',
            task_type='maintenance',
            property_ref=test_property,
            booking=test_booking,
            created_by=test_user
        )

        # Create photos for both tasks
        TaskImage.objects.create(
            task=cleaning_task,
            uploaded_by=test_user,
            photo_type='before',
            sequence_number=1
        )
        TaskImage.objects.create(
            task=maintenance_task,
            uploaded_by=test_user,
            photo_type='before',
            sequence_number=1
        )

        # Get cleaning photos only
        cleaning_photos = TaskImage.objects.filter(
            task__task_type='cleaning'
        )
        assert cleaning_photos.count() == 1
        assert cleaning_photos.first().task == cleaning_task

        # Get maintenance photos only
        maintenance_photos = TaskImage.objects.filter(
            task__task_type='maintenance'
        )
        assert maintenance_photos.count() == 1
        assert maintenance_photos.first().task == maintenance_task


class TestTaskImageSerializerEnhancements:
    """Test TaskImageSerializer with before/after photo fields."""

    @pytest.mark.django_db
    def test_serializer_includes_new_fields(self, test_task, test_user):
        """Test that serializer includes all new before/after photo fields."""
        photo = TaskImage.objects.create(
            task=test_task,
            uploaded_by=test_user,
            photo_type='before',
            photo_status='approved',
            description='Test description',
            sequence_number=1,
            is_primary=True
        )

        serializer = TaskImageSerializer(photo)
        data = serializer.data

        # Check that all new fields are included
        assert 'photo_type' in data
        assert 'photo_type_display' in data
        assert 'photo_status' in data
        assert 'photo_status_display' in data
        assert 'sequence_number' in data
        assert 'is_primary' in data
        assert 'description' in data

        # Check values
        assert data['photo_type'] == 'before'
        assert data['photo_type_display'] == 'Before'
        assert data['photo_status'] == 'approved'
        assert data['photo_status_display'] == 'Approved'
        assert data['description'] == 'Test description'
        assert data['sequence_number'] == 1
        assert data['is_primary'] is True
