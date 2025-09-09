"""
Integration tests for checklist workflow
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from api.models import Task, TaskChecklist, ChecklistTemplate, ChecklistResponse, ChecklistItem, Profile


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear cache before and after each test"""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestChecklistWorkflowIntegration:
    """Integration tests for complete checklist workflow"""
    
    def test_checklist_assignment_to_completion_workflow(self):
        """Test complete workflow from assignment to completion"""
        # Create user and profile
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        profile = Profile.objects.create(
            user=user,
            role='staff',
            first_name='Test',
            last_name='User'
        )
        
        # Create task
        task = Task.objects.create(
            title="Test Cleaning Task",
            description="Test task for cleaning",
            task_type="cleaning",
            assigned_to=user
        )
        
        # Create template and items
        template = ChecklistTemplate.objects.create(
            name="Guest Turnover",
            description="Guest turnover checklist"
        )
        
        items = [
            ChecklistItem.objects.create(
                template=template,
                title="Check for guest belongings",
                description="Look for any items left behind"
            ),
            ChecklistItem.objects.create(
                template=template,
                title="Remove all trash",
                description="Empty all trash bins"
            ),
            ChecklistItem.objects.create(
                template=template,
                title="Strip all bedding",
                description="Remove all bedding for cleaning"
            )
        ]
        
        # Assign checklist
        from api.management.commands.assign_checklists import Command
        command = Command()
        checklist = command._create_checklist_for_task(task, template)
        
        # Verify checklist was created
        assert TaskChecklist.objects.count() == 1
        assert ChecklistResponse.objects.count() == 3
        
        # Verify initial state
        responses = ChecklistResponse.objects.filter(checklist=checklist)
        for response in responses:
            assert not response.is_completed
        
        # Complete checklist items
        for i, response in enumerate(responses):
            response.is_completed = True
            response.save()
        
        # Verify completion
        completed_responses = ChecklistResponse.objects.filter(
            checklist=checklist,
            is_completed=True
        )
        assert completed_responses.count() == 3
        
        # Verify checklist completion status
        checklist.refresh_from_db()
        # Note: Add completion logic to TaskChecklist model if needed
    
    def test_checklist_api_endpoints(self):
        """Test checklist API endpoints"""
        # Create user and profile
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile = Profile.objects.create(
            user=user,
            role='staff'
        )
        
        # Create task and checklist
        task = Task.objects.create(
            title="Test Task",
            task_type="cleaning",
            assigned_to=user
        )
        
        template = ChecklistTemplate.objects.create(
            name="Test Template",
            description="Test checklist"
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
        
        # Test API client
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Test checklist list endpoint
        response = client.get('/api/staff/checklist/')
        assert response.status_code == status.HTTP_200_OK
        
        # Test checklist detail endpoint
        response = client.get(f'/api/staff/checklist/{checklist.id}/')
        assert response.status_code == status.HTTP_200_OK
        
        # Test checklist response update
        response = client.patch(
            f'/api/staff/checklist/{checklist.id}/responses/{response.id}/',
            {'is_completed': True}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify update
        response.refresh_from_db()
        assert response.is_completed
    
    def test_checklist_permissions(self):
        """Test checklist permissions"""
        # Create users
        staff_user = User.objects.create_user(
            username='staff',
            password='testpass123'
        )
        staff_profile = Profile.objects.create(
            user=staff_user,
            role='staff'
        )
        
        manager_user = User.objects.create_user(
            username='manager',
            password='testpass123'
        )
        manager_profile = Profile.objects.create(
            user=manager_user,
            role='manager'
        )
        
        # Create task and checklist
        task = Task.objects.create(
            title="Test Task",
            task_type="cleaning",
            assigned_to=staff_user
        )
        
        template = ChecklistTemplate.objects.create(
            name="Test Template"
        )
        
        checklist = TaskChecklist.objects.create(
            task=task,
            template=template
        )
        
        # Test staff user can access their checklist
        client = APIClient()
        client.force_authenticate(user=staff_user)
        
        response = client.get(f'/api/staff/checklist/{checklist.id}/')
        assert response.status_code == status.HTTP_200_OK
        
        # Test manager can access all checklists
        client.force_authenticate(user=manager_user)
        
        response = client.get(f'/api/staff/checklist/{checklist.id}/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_checklist_photo_upload(self):
        """Test checklist photo upload functionality"""
        # Create user and profile
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile = Profile.objects.create(
            user=user,
            role='staff'
        )
        
        # Create task and checklist
        task = Task.objects.create(
            title="Test Task",
            task_type="cleaning",
            assigned_to=user
        )
        
        template = ChecklistTemplate.objects.create(
            name="Test Template"
        )
        
        item = ChecklistItem.objects.create(
            template=template,
            title="Test Item",
            requires_photo=True
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
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Create test image
        from django.core.files.uploadedfile import SimpleUploadedFile
        test_image = SimpleUploadedFile(
            "test_image.jpg",
            b"fake image content",
            content_type="image/jpeg"
        )
        
        # Test photo upload endpoint
        upload_response = client.post(
            '/api/staff/checklist/photo/upload/',
            {
                'response_id': response.id,
                'photo': test_image
            },
            format='multipart'
        )
        
        # Verify upload was successful
        assert upload_response.status_code == status.HTTP_200_OK
        
        # Verify photo was saved
        response.refresh_from_db()
        assert response.photo is not None
        assert response.photo.name is not None
    
    def test_checklist_bulk_operations(self):
        """Test bulk operations on checklists"""
        # Create user and profile
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile = Profile.objects.create(
            user=user,
            role='staff'
        )
        
        # Create multiple tasks and checklists
        tasks = []
        checklists = []
        
        for i in range(5):
            task = Task.objects.create(
                title=f"Task {i}",
                task_type="cleaning",
                assigned_to=user
            )
            tasks.append(task)
            
            template = ChecklistTemplate.objects.create(
                name=f"Template {i}"
            )
            
            checklist = TaskChecklist.objects.create(
                task=task,
                template=template
            )
            checklists.append(checklist)
        
        # Test bulk checklist retrieval
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/staff/checklist/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 5
        
        # Test bulk completion
        completion_data = {
            'checklist_ids': [c.id for c in checklists],
            'complete': True
        }
        
        response = client.post(
            '/api/staff/checklist/bulk-complete/',
            completion_data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify all checklists were completed
        for checklist in checklists:
            responses = ChecklistResponse.objects.filter(checklist=checklist)
            for response in responses:
                assert response.is_completed


@pytest.mark.django_db
class TestChecklistErrorHandling:
    """Test error handling in checklist system"""
    
    def test_invalid_checklist_access(self):
        """Test accessing non-existent checklist"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile = Profile.objects.create(
            user=user,
            role='staff'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Try to access non-existent checklist
        response = client.get('/api/staff/checklist/99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_unauthorized_checklist_access(self):
        """Test accessing checklist without permission"""
        # Create users
        staff_user = User.objects.create_user(
            username='staff',
            password='testpass123'
        )
        staff_profile = Profile.objects.create(
            user=staff_user,
            role='staff'
        )
        
        other_user = User.objects.create_user(
            username='other',
            password='testpass123'
        )
        other_profile = Profile.objects.create(
            user=other_user,
            role='staff'
        )
        
        # Create task assigned to staff_user
        task = Task.objects.create(
            title="Test Task",
            task_type="cleaning",
            assigned_to=staff_user
        )
        
        template = ChecklistTemplate.objects.create(
            name="Test Template"
        )
        
        checklist = TaskChecklist.objects.create(
            task=task,
            template=template
        )
        
        # Try to access with other user
        client = APIClient()
        client.force_authenticate(user=other_user)
        
        response = client.get(f'/api/staff/checklist/{checklist.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_invalid_photo_upload(self):
        """Test invalid photo upload"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile = Profile.objects.create(
            user=user,
            role='staff'
        )
        
        # Create task and checklist
        task = Task.objects.create(
            title="Test Task",
            task_type="cleaning",
            assigned_to=user
        )
        
        template = ChecklistTemplate.objects.create(
            name="Test Template"
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
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Test invalid file type
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"not an image",
            content_type="text/plain"
        )
        
        upload_response = client.post(
            '/api/staff/checklist/photo/upload/',
            {
                'response_id': response.id,
                'photo': invalid_file
            },
            format='multipart'
        )
        
        assert upload_response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test missing file
        upload_response = client.post(
            '/api/staff/checklist/photo/upload/',
            {
                'response_id': response.id
            },
            format='multipart'
        )
        
        assert upload_response.status_code == status.HTTP_400_BAD_REQUEST
