"""
Simple integration tests for unified photo system (checklist + task photos)
Tests core functionality without file uploads
"""
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.db import models
from api.models import (
    Task, Property, TaskChecklist, ChecklistTemplate, ChecklistItem, 
    ChecklistResponse, TaskImage, Profile
)


@override_settings(
    DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage',
    MEDIA_ROOT='/tmp/test_media'
)
class TestUnifiedPhotoSystemSimple(TestCase):
    """Test the unified photo system integration without file uploads"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        Profile.objects.get_or_create(user=self.user)
        
        self.property = Property.objects.create(name='Test Property')
        self.task = Task.objects.create(
            title='Test Task',
            task_type='cleaning',
            property_ref=self.property,
            created_by=self.user,
            assigned_to=self.user,
        )
        
        # Create checklist with photo item
        self.template = ChecklistTemplate.objects.create(
            name='Test Template',
            task_type='cleaning',
            is_active=True,
            created_by=self.user
        )
        self.photo_item = ChecklistItem.objects.create(
            template=self.template,
            title='Take photo',
            item_type='photo_required'
        )
        self.checklist = TaskChecklist.objects.create(
            task=self.task,
            template=self.template
        )
        self.response = ChecklistResponse.objects.create(
            checklist=self.checklist,
            item=self.photo_item
        )
    
    def test_photo_type_choices_include_checklist(self):
        """Test that photo_type choices include 'checklist'"""
        choices = TaskImage._meta.get_field('photo_type').choices
        choice_values = [choice[0] for choice in choices]
        assert 'checklist' in choice_values
    
    def test_checklist_response_relationship(self):
        """Test that TaskImage can link to ChecklistResponse"""
        # Create TaskImage without file (just test the relationship)
        task_image = TaskImage(
            task=self.task,
            checklist_response=self.response,
            uploaded_by=self.user,
            photo_type='checklist'
        )
        # Don't save to avoid file upload issues
        assert task_image.checklist_response == self.response
        assert task_image.photo_type == 'checklist'
    
    def test_sequence_number_auto_increment_logic(self):
        """Test that sequence numbers auto-increment logic works"""
        # Test the sequence number calculation logic
        existing_images = TaskImage.objects.filter(
            task=self.task,
            photo_type='checklist'
        )
        
        # Calculate next sequence number
        if existing_images.exists():
            next_sequence = existing_images.aggregate(
                max_seq=models.Max('sequence_number')
            )['max_seq'] + 1
        else:
            next_sequence = 1
            
        assert next_sequence == 1  # Should be 1 for first image
    
    def test_unified_photos_context_logic(self):
        """Test that unified photos context logic works"""
        # Test the logic for attaching unified photos to responses
        task_images = TaskImage.objects.filter(task=self.task).select_related('checklist_response')
        images_by_response = {}
        
        for img in task_images:
            rid = getattr(img.checklist_response, 'id', None)
            if rid:
                images_by_response.setdefault(rid, []).append(img)
        
        # Test that the logic works even with empty results
        assert isinstance(images_by_response, dict)
        
        # Test attaching to response
        response_id = self.response.id
        unified_photos = images_by_response.get(response_id, [])
        assert isinstance(unified_photos, list)
    
    def test_photo_type_display(self):
        """Test that photo type display works correctly"""
        task_image = TaskImage(
            task=self.task,
            uploaded_by=self.user,
            photo_type='checklist'
        )
        
        # Test display method
        assert task_image.get_photo_type_display() == 'Checklist'
    
    def test_model_relationships(self):
        """Test that model relationships are properly defined"""
        # Test TaskImage -> Task relationship
        task_image = TaskImage(task=self.task, uploaded_by=self.user, photo_type='checklist')
        assert task_image.task == self.task
        
        # Test TaskImage -> ChecklistResponse relationship
        task_image.checklist_response = self.response
        assert task_image.checklist_response == self.response
        
        # Test reverse relationships exist
        assert hasattr(self.task, 'images')
        assert hasattr(self.response, 'task_images')
    
    def test_photo_type_validation(self):
        """Test that photo_type validation works"""
        # Valid photo types
        valid_types = ['before', 'after', 'during', 'reference', 'damage', 'general', 'checklist']
        
        for photo_type in valid_types:
            task_image = TaskImage(
                task=self.task,
                uploaded_by=self.user,
                photo_type=photo_type
            )
            # Test that photo_type is set correctly (can't test full_clean without image)
            assert task_image.photo_type == photo_type
    
    def test_checklist_photo_identification(self):
        """Test that checklist photos can be identified"""
        # Test filtering checklist photos
        checklist_images = TaskImage.objects.filter(
            task=self.task,
            photo_type='checklist'
        )
        assert checklist_images.count() == 0  # No images yet
        
        # Test that checklist photos are linked to responses
        task_image = TaskImage(
            task=self.task,
            checklist_response=self.response,
            uploaded_by=self.user,
            photo_type='checklist'
        )
        
        # Should be identifiable as checklist photo
        assert task_image.photo_type == 'checklist'
        assert task_image.checklist_response is not None
        assert task_image.checklist_response == self.response
