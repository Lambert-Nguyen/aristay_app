"""
Unit tests for checklist photo upload functionality
"""
import pytest
from django.test import Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from api.models import Task, TaskChecklist, ChecklistTemplate, ChecklistItem, ChecklistResponse, ChecklistPhoto, Profile
from PIL import Image
import io

def create_test_image():
    """Create a valid test image for Cloudinary uploads"""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes.getvalue()


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear cache before and after each test"""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestChecklistPhotoUpload:
    """Test checklist photo upload functionality"""
    
    def test_photo_upload_success(self):
        """Test successful photo upload"""
        # Create user and profile
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'staff'}
        )
        
        # Create task and checklist
        task = Task.objects.create(
            title="Test Task",
            task_type="cleaning",
            assigned_to=user
        )
        
        template = ChecklistTemplate.objects.create(
            name="Test Template",
            description="Test checklist",
            created_by=user
        )
        
        item = ChecklistItem.objects.create(
            template=template,
            title="Test Item"
        )
        
        checklist = TaskChecklist.objects.create(
            task=task,
            template=template
        )
        
        response = ChecklistResponse.objects.create(
            checklist=checklist,
            item=item
        )
        
        # Test photo upload
        client = Client()
        client.force_login(user)
        
        test_image = SimpleUploadedFile(
            "test_image.jpg",
            create_test_image(),
            content_type="image/jpeg"
        )
        
        response_data = client.post('/api/staff/checklist/photo/upload/', {
            'item_id': response.id,
            'photo': test_image
        }, HTTP_HOST='localhost:8000')
        
        assert response_data.status_code == 200
        
        # Verify photo was created
        photos = ChecklistPhoto.objects.filter(response=response)
        assert photos.count() == 1
        
        photo = photos.first()
        assert photo.uploaded_by == user
        assert photo.image.name is not None
    
    def test_photo_upload_missing_item_id(self):
        """Test photo upload with missing item_id"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'staff'}
        )
        
        client = Client()
        client.force_login(user)
        
        test_image = SimpleUploadedFile(
            "test_image.jpg",
            create_test_image(),
            content_type="image/jpeg"
        )
        
        response_data = client.post('/api/staff/checklist/photo/upload/', {
            'photo': test_image
        }, HTTP_HOST='localhost:8000')
        
        assert response_data.status_code == 400
        assert 'Missing item_id' in response_data.content.decode()
    
    def test_photo_upload_missing_photo(self):
        """Test photo upload with missing photo"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'staff'}
        )
        
        # Create test data
        task = Task.objects.create(
            title="Test Task",
            task_type="cleaning",
            assigned_to=user
        )
        
        template = ChecklistTemplate.objects.create(
            name="Test Template",
            created_by=user
        )
        
        item = ChecklistItem.objects.create(
            template=template,
            title="Test Item"
        )
        
        checklist = TaskChecklist.objects.create(
            task=task,
            template=template
        )
        
        response = ChecklistResponse.objects.create(
            checklist=checklist,
            item=item
        )
        
        client = Client()
        client.force_login(user)
        
        response_data = client.post('/api/staff/checklist/photo/upload/', {
            'item_id': response.id
        }, HTTP_HOST='localhost:8000')
        
        assert response_data.status_code == 400
        assert 'Missing item_id or photo' in response_data.content.decode()
    
    def test_photo_upload_invalid_file_type(self):
        """Test photo upload with invalid file type"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'staff'}
        )
        
        # Create test data
        task = Task.objects.create(
            title="Test Task",
            task_type="cleaning",
            assigned_to=user
        )
        
        template = ChecklistTemplate.objects.create(
            name="Test Template",
            created_by=user
        )
        
        item = ChecklistItem.objects.create(
            template=template,
            title="Test Item"
        )
        
        checklist = TaskChecklist.objects.create(
            task=task,
            template=template
        )
        
        response = ChecklistResponse.objects.create(
            checklist=checklist,
            item=item
        )
        
        client = Client()
        client.force_login(user)
        
        # Test with text file instead of image
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"not an image",
            content_type="text/plain"
        )
        
        response_data = client.post('/api/staff/checklist/photo/upload/', {
            'item_id': response.id,
            'photo': invalid_file
        }, HTTP_HOST='localhost:8000')
        
        # The backend validates file type and rejects invalid files
        assert response_data.status_code == 400
    
    def test_photo_upload_permission_denied(self):
        """Test photo upload with insufficient permissions"""
        # Create users
        staff_user = User.objects.create_user(
            username='staff',
            password='testpass123'
        )
        staff_profile, created = Profile.objects.get_or_create(
            user=staff_user,
            defaults={'role': 'staff'}
        )
        
        other_user = User.objects.create_user(
            username='other',
            password='testpass123'
        )
        other_profile, created = Profile.objects.get_or_create(
            user=other_user,
            defaults={'role': 'staff'}
        )
        
        # Create task assigned to staff_user
        task = Task.objects.create(
            title="Test Task",
            task_type="cleaning",
            assigned_to=staff_user
        )
        
        template = ChecklistTemplate.objects.create(
            name="Test Template",
            created_by=staff_user
        )
        
        item = ChecklistItem.objects.create(
            template=template,
            title="Test Item"
        )
        
        checklist = TaskChecklist.objects.create(
            task=task,
            template=template
        )
        
        response = ChecklistResponse.objects.create(
            checklist=checklist,
            item=item
        )
        
        # Try to upload with other user
        client = Client()
        client.force_login(other_user)
        
        test_image = SimpleUploadedFile(
            "test_image.jpg",
            create_test_image(),
            content_type="image/jpeg"
        )
        
        response_data = client.post('/api/staff/checklist/photo/upload/', {
            'item_id': response.id,
            'photo': test_image
        }, HTTP_HOST='localhost:8000')
        
        # Should be denied due to permissions
        assert response_data.status_code == 403
        assert 'Permission denied' in response_data.content.decode()
    
    def test_photo_upload_nonexistent_item(self):
        """Test photo upload with non-existent item"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'staff'}
        )
        
        client = Client()
        client.force_login(user)
        
        test_image = SimpleUploadedFile(
            "test_image.jpg",
            create_test_image(),
            content_type="image/jpeg"
        )
        
        response_data = client.post('/api/staff/checklist/photo/upload/', {
            'item_id': 99999,  # Non-existent ID
            'photo': test_image
        }, HTTP_HOST='localhost:8000')
        
        # API returns 400 for non-existent item, not 404
        assert response_data.status_code == 400
    
    def test_photo_upload_large_file(self):
        """Test photo upload with large file"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'staff'}
        )
        
        # Create test data
        task = Task.objects.create(
            title="Test Task",
            task_type="cleaning",
            assigned_to=user
        )
        
        template = ChecklistTemplate.objects.create(
            name="Test Template",
            created_by=user
        )
        
        item = ChecklistItem.objects.create(
            template=template,
            title="Test Item"
        )
        
        checklist = TaskChecklist.objects.create(
            task=task,
            template=template
        )
        
        response = ChecklistResponse.objects.create(
            checklist=checklist,
            item=item
        )
        
        client = Client()
        client.force_login(user)
        
        # Create large file (10MB)
        large_content = b"x" * (10 * 1024 * 1024)
        large_file = SimpleUploadedFile(
            "large_image.jpg",
            large_content,
            content_type="image/jpeg"
        )
        
        response_data = client.post('/api/staff/checklist/photo/upload/', {
            'item_id': response.id,
            'photo': large_file
        }, HTTP_HOST='localhost:8000')
        
        # Should fail as the file is too large (10MB > 5MB limit)
        assert response_data.status_code == 400


@pytest.mark.django_db
class TestChecklistPhotoRemoval:
    """Test checklist photo removal functionality"""
    
    def test_photo_removal_success(self):
        """Test successful photo removal"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'staff'}
        )
        
        # Create test data
        task = Task.objects.create(
            title="Test Task",
            task_type="cleaning",
            assigned_to=user
        )
        
        template = ChecklistTemplate.objects.create(
            name="Test Template",
            created_by=user
        )
        
        item = ChecklistItem.objects.create(
            template=template,
            title="Test Item"
        )
        
        checklist = TaskChecklist.objects.create(
            task=task,
            template=template
        )
        
        response = ChecklistResponse.objects.create(
            checklist=checklist,
            item=item
        )
        
        # Create photo
        test_image = SimpleUploadedFile(
            "test_image.jpg",
            create_test_image(),
            content_type="image/jpeg"
        )
        
        photo = ChecklistPhoto.objects.create(
            response=response,
            image=test_image,
            uploaded_by=user
        )
        
        client = Client()
        client.force_login(user)
        
        # Remove photo
        response_data = client.post('/api/staff/checklist/photo/remove/', {
            'item_id': response.id,
            'photo_url': photo.image.url
        }, content_type='application/json', HTTP_HOST='localhost:8000')
        
        assert response_data.status_code == 200
        
        # Verify photo was removed
        photos = ChecklistPhoto.objects.filter(response=response)
        assert photos.count() == 0
    
    def test_photo_removal_missing_parameters(self):
        """Test photo removal with missing parameters"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'staff'}
        )
        
        client = Client()
        client.force_login(user)
        
        response_data = client.post('/api/staff/checklist/photo/remove/', {
            'item_id': 1
        }, content_type='application/json', HTTP_HOST='localhost:8000')
        
        assert response_data.status_code == 400
        assert 'Missing item_id or photo_url' in response_data.content.decode()
    
    def test_photo_removal_nonexistent_photo(self):
        """Test photo removal with non-existent photo"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'staff'}
        )
        
        # Create test data
        task = Task.objects.create(
            title="Test Task",
            task_type="cleaning",
            assigned_to=user
        )
        
        template = ChecklistTemplate.objects.create(
            name="Test Template",
            created_by=user
        )
        
        item = ChecklistItem.objects.create(
            template=template,
            title="Test Item"
        )
        
        checklist = TaskChecklist.objects.create(
            task=task,
            template=template
        )
        
        response = ChecklistResponse.objects.create(
            checklist=checklist,
            item=item
        )
        
        client = Client()
        client.force_login(user)
        
        response_data = client.post('/api/staff/checklist/photo/remove/', {
            'item_id': response.id,
            'photo_url': '/media/nonexistent.jpg'
        }, content_type='application/json', HTTP_HOST='localhost:8000')
        
        # API returns 404 when photo doesn't exist
        assert response_data.status_code == 404
