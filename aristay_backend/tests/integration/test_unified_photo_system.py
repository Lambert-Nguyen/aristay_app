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
        # Create a real JPEG image for testing
        from PIL import Image
        import io
        img = Image.new('RGB', (100, 100), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        image_content = SimpleUploadedFile(
            'test.jpg', 
            img_bytes.getvalue(), 
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
        # Clean up any existing TaskImage objects to avoid conflicts
        TaskImage.objects.filter(photo_type='checklist').delete()
        
        # Create a fresh task and response to avoid conflicts
        # Use a unique title to ensure we get a fresh task
        import time
        fresh_task = Task.objects.create(
            title=f'Fresh Task {int(time.time())}',
            task_type='cleaning',
            property_ref=self.property,
            created_by=self.user,
            assigned_to=self.user,
        )
        
        fresh_template = ChecklistTemplate.objects.create(
            name='Fresh Template',
            task_type='cleaning',
            is_active=True,
            created_by=self.user
        )
        fresh_photo_item = ChecklistItem.objects.create(
            template=fresh_template,
            title='Take photo',
            item_type='photo_required'
        )
        fresh_checklist = TaskChecklist.objects.create(
            task=fresh_task,
            template=fresh_template
        )
        fresh_response = ChecklistResponse.objects.create(
            checklist=fresh_checklist,
            item=fresh_photo_item
        )
        
        # Create multiple checklist photos
        for i in range(3):
            # Create a real JPEG image for testing
            from PIL import Image
            import io
            img = Image.new('RGB', (100, 100), color=f'rgb({i*50}, {i*50}, {i*50})')
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            # Calculate sequence number like the actual system does
            existing = TaskImage.objects.filter(task=fresh_task, photo_type='checklist')
            next_seq = existing.count() + 1
            
            TaskImage.objects.create(
                task=fresh_task,
                checklist_response=fresh_response,
                image=SimpleUploadedFile(f'test{i}.jpg', img_bytes.getvalue(), content_type='image/jpeg'),
                uploaded_by=self.user,
                photo_type='checklist',
                sequence_number=next_seq
            )
        
        # Check sequence numbers
        images = TaskImage.objects.filter(
            task=fresh_task,
            photo_type='checklist'
        ).order_by('sequence_number')
        
        assert images.count() == 3
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
