"""
Integration tests for unified photo system (checklist + task photos)
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from api.models import (
    Task, Property, TaskChecklist, ChecklistTemplate, ChecklistItem, 
    ChecklistResponse, TaskImage, Profile
)


class TestUnifiedPhotoSystem(TestCase):
    """Test the unified photo system integration"""
    
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
        
        self.client = Client()
        # Use force_login to bypass Axes authentication issues in tests
        self.client.force_login(self.user)
    
    def test_checklist_upload_creates_taskimage(self):
        """Test that checklist photo upload creates TaskImage"""
        # Upload photo via staff endpoint
        image_content = SimpleUploadedFile(
            'test.jpg', 
            b'\xff\xd8\xff\xd9', 
            content_type='image/jpeg'
        )
        
        response = self.client.post('/api/staff/checklist/photo/upload/', {
            'item_id': self.response.id,
            'photo': image_content
        })
        
        assert response.status_code in [200, 302]
        
        # Verify TaskImage was created
        task_images = TaskImage.objects.filter(
            task=self.task,
            checklist_response=self.response,
            photo_type='checklist'
        )
        assert task_images.count() == 1
        
        task_image = task_images.first()
        assert task_image.uploaded_by == self.user
        assert task_image.photo_type == 'checklist'
        assert task_image.sequence_number == 1
    
    def test_checklist_remove_deletes_taskimage(self):
        """Test that checklist photo removal deletes TaskImage"""
        # Create a TaskImage first
        task_image = TaskImage.objects.create(
            task=self.task,
            checklist_response=self.response,
            image=SimpleUploadedFile(
                'test.jpg', 
                b'\xff\xd8\xff\xd9', 
                content_type='image/jpeg'
            ),
            uploaded_by=self.user,
            photo_type='checklist'
        )
        
        # Remove photo via staff endpoint
        response = self.client.post('/api/staff/checklist/photo/remove/', 
            data={'item_id': self.response.id, 'photo_url': task_image.image.url},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        # Verify TaskImage was deleted
        assert not TaskImage.objects.filter(id=task_image.id).exists()
    
    def test_unified_photos_in_template_context(self):
        """Test that unified photos are attached to response in template context"""
        # Create some TaskImages
        TaskImage.objects.create(
            task=self.task,
            checklist_response=self.response,
            image=SimpleUploadedFile('test1.jpg', b'\xff\xd8\xff\xd9', content_type='image/jpeg'),
            uploaded_by=self.user,
            photo_type='checklist'
        )
        TaskImage.objects.create(
            task=self.task,
            image=SimpleUploadedFile('test2.jpg', b'\xff\xd8\xff\xd9', content_type='image/jpeg'),
            uploaded_by=self.user,
            photo_type='before'
        )
        
        # Access task detail view
        response = self.client.get(f'/api/staff/tasks/{self.task.id}/')
        assert response.status_code == 200
        
        # Check that unified_photos is attached to response
        # This would be tested in the template rendering
        assert 'unified_photos' in str(response.content) or 'All Task Photos' in str(response.content)
    
    def test_photo_type_choices_include_checklist(self):
        """Test that photo_type choices include 'checklist'"""
        choices = TaskImage._meta.get_field('photo_type').choices
        choice_values = [choice[0] for choice in choices]
        assert 'checklist' in choice_values
    
    def test_checklist_response_relationship(self):
        """Test that TaskImage can link to ChecklistResponse"""
        task_image = TaskImage.objects.create(
            task=self.task,
            checklist_response=self.response,
            image=SimpleUploadedFile('test.jpg', b'\xff\xd8\xff\xd9', content_type='image/jpeg'),
            uploaded_by=self.user,
            photo_type='checklist'
        )
        
        assert task_image.checklist_response == self.response
        assert task_image in self.response.task_images.all()
    
    def test_sequence_number_auto_increment(self):
        """Test that sequence numbers auto-increment for checklist photos"""
        # Create multiple checklist photos
        for i in range(3):
            TaskImage.objects.create(
                task=self.task,
                checklist_response=self.response,
                image=SimpleUploadedFile(f'test{i}.jpg', b'\xff\xd8\xff\xd9', content_type='image/jpeg'),
                uploaded_by=self.user,
                photo_type='checklist'
            )
        
        # Check sequence numbers
        images = TaskImage.objects.filter(
            task=self.task,
            photo_type='checklist'
        ).order_by('sequence_number')
        
        assert images[0].sequence_number == 1
        assert images[1].sequence_number == 2
        assert images[2].sequence_number == 3
    
    def test_legacy_checklist_photo_fallback(self):
        """Test that removal falls back to legacy ChecklistPhoto"""
        from api.models import ChecklistPhoto
        
        # Create legacy ChecklistPhoto
        legacy_photo = ChecklistPhoto.objects.create(
            response=self.response,
            image=SimpleUploadedFile('legacy.jpg', b'\xff\xd8\xff\xd9', content_type='image/jpeg'),
            uploaded_by=self.user
        )
        
        # Try to remove it
        response = self.client.post('/api/staff/checklist/photo/remove/', 
            data={'item_id': self.response.id, 'photo_url': legacy_photo.image.url},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        assert not ChecklistPhoto.objects.filter(id=legacy_photo.id).exists()
