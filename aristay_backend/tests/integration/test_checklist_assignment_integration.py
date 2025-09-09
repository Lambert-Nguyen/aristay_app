"""
Integration tests for checklist assignment system
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from api.models import (
    Task, TaskChecklist, ChecklistTemplate, ChecklistItem, ChecklistResponse, 
    ChecklistPhoto, UserProfile, AuditEvent
)


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear cache before and after each test"""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestChecklistAssignmentIntegration:
    """Integration tests for checklist assignment system"""
    
    def test_complete_checklist_workflow(self):
        """Test complete workflow from assignment to completion"""
        # Create user and profile
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        profile = UserProfile.objects.create(
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
            description="Guest turnover checklist",
            task_type="cleaning"
        )
        
        items = [
            ChecklistItem.objects.create(
                template=template,
                title="Check for guest belongings",
                description="Look for any items left behind",
                item_type="check"
            ),
            ChecklistItem.objects.create(
                template=template,
                title="Remove all trash",
                description="Empty all trash bins",
                item_type="check"
            ),
            ChecklistItem.objects.create(
                template=template,
                title="Strip all bedding",
                description="Remove all bedding for cleaning",
                item_type="check"
            )
        ]
        
        # Assign checklist using management command
        call_command('assign_checklists')
        
        # Verify checklist was created
        checklist = TaskChecklist.objects.get(task=task, template=template)
        assert checklist is not None
        
        # Verify responses were created
        responses = ChecklistResponse.objects.filter(checklist=checklist)
        assert responses.count() == 3
        
        # Verify initial state
        for response in responses:
            assert not response.is_completed
        
        # Complete checklist items
        for response in responses:
            response.is_completed = True
            response.completed_at = timezone.now()
            response.completed_by = user
            response.save()
        
        # Verify completion
        completed_responses = ChecklistResponse.objects.filter(
            checklist=checklist,
            is_completed=True
        )
        assert completed_responses.count() == 3
        
        # Test photo upload for one item
        response = responses.first()
        test_image = SimpleUploadedFile(
            "test_image.jpg",
            b"fake image content",
            content_type="image/jpeg"
        )
        
        client = Client()
        client.force_login(user)
        
        photo_response = client.post('/api/staff/checklist/photo/upload/', {
            'item_id': response.id,
            'photo': test_image
        }, HTTP_HOST='localhost:8000')
        
        assert photo_response.status_code == 200
        
        # Verify photo was created
        photos = ChecklistPhoto.objects.filter(response=response)
        assert photos.count() == 1
        
        # Verify audit events were created
        audit_events = AuditEvent.objects.filter(
            object_type__in=['TaskChecklist', 'ChecklistResponse', 'ChecklistPhoto']
        )
        assert audit_events.count() > 0
    
    def test_checklist_assignment_api(self):
        """Test checklist assignment via API"""
        # Create user and profile
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile = UserProfile.objects.create(
            user=user,
            role='staff'
        )
        
        # Create task and template
        task = Task.objects.create(
            title="Test Task",
            task_type="cleaning",
            assigned_to=user
        )
        
        template = ChecklistTemplate.objects.create(
            name="Test Template",
            description="Test checklist",
            task_type="cleaning"
        )
        
        item = ChecklistItem.objects.create(
            template=template,
            title="Test Item"
        )
        
        # Test API client
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Test checklist assignment
        response = client.post('/api/staff/checklist/assign/', {
            'task_id': task.id,
            'template_id': template.id
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify checklist was created
        checklist = TaskChecklist.objects.get(task=task, template=template)
        assert checklist is not None
        
        # Verify response was created
        responses = ChecklistResponse.objects.filter(checklist=checklist)
        assert responses.count() == 1
    
    def test_checklist_bulk_operations(self):
        """Test bulk operations on checklists"""
        # Create user and profile
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile = UserProfile.objects.create(
            user=user,
            role='staff'
        )
        
        # Create multiple tasks and checklists
        tasks = []
        checklists = []
        
        for i in range(3):
            task = Task.objects.create(
                title=f"Task {i}",
                task_type="cleaning",
                assigned_to=user
            )
            tasks.append(task)
            
            template = ChecklistTemplate.objects.create(
                name=f"Template {i}",
                task_type="cleaning"
            )
            
            item = ChecklistItem.objects.create(
                template=template,
                title=f"Item {i}"
            )
            
            checklist = TaskChecklist.objects.create(
                task=task,
                template=template
            )
            checklists.append(checklist)
            
            ChecklistResponse.objects.create(
                checklist=checklist,
                item=item
            )
        
        # Test bulk checklist retrieval
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/staff/checklist/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        
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
    
    def test_checklist_permissions(self):
        """Test checklist permissions"""
        # Create users
        staff_user = User.objects.create_user(
            username='staff',
            password='testpass123'
        )
        staff_profile = UserProfile.objects.create(
            user=staff_user,
            role='staff'
        )
        
        manager_user = User.objects.create_user(
            username='manager',
            password='testpass123'
        )
        manager_profile = UserProfile.objects.create(
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
            name="Test Template",
            task_type="cleaning"
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
        
        # Test staff user can access their checklist
        client = APIClient()
        client.force_authenticate(user=staff_user)
        
        response = client.get(f'/api/staff/checklist/{checklist.id}/')
        assert response.status_code == status.HTTP_200_OK
        
        # Test manager can access all checklists
        client.force_authenticate(user=manager_user)
        
        response = client.get(f'/api/staff/checklist/{checklist.id}/')
        assert response.status_code == status.HTTP_200_OK
        
        # Test other staff user cannot access
        other_staff = User.objects.create_user(
            username='other_staff',
            password='testpass123'
        )
        other_profile = UserProfile.objects.create(
            user=other_staff,
            role='staff'
        )
        
        client.force_authenticate(user=other_staff)
        
        response = client.get(f'/api/staff/checklist/{checklist.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_checklist_error_handling(self):
        """Test error handling in checklist system"""
        # Create user and profile
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile = UserProfile.objects.create(
            user=user,
            role='staff'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Test accessing non-existent checklist
        response = client.get('/api/staff/checklist/99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test invalid photo upload
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"not an image",
            content_type="text/plain"
        )
        
        response = client.post('/api/staff/checklist/photo/upload/', {
            'item_id': 99999,
            'photo': invalid_file
        }, format='multipart')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_checklist_audit_trail(self):
        """Test audit trail for checklist operations"""
        # Create user and profile
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile = UserProfile.objects.create(
            user=user,
            role='staff'
        )
        
        # Create task and template
        task = Task.objects.create(
            title="Test Task",
            task_type="cleaning",
            assigned_to=user
        )
        
        template = ChecklistTemplate.objects.create(
            name="Test Template",
            task_type="cleaning"
        )
        
        item = ChecklistItem.objects.create(
            template=template,
            title="Test Item"
        )
        
        # Assign checklist
        call_command('assign_checklists')
        
        # Verify audit events were created
        checklist_audit = AuditEvent.objects.filter(
            event_type='create',
            object_type='TaskChecklist'
        )
        assert checklist_audit.exists()
        
        response_audit = AuditEvent.objects.filter(
            event_type='create',
            object_type='ChecklistResponse'
        )
        assert response_audit.exists()
        
        # Test photo upload audit
        checklist = TaskChecklist.objects.get(task=task, template=template)
        response = ChecklistResponse.objects.get(checklist=checklist, item=item)
        
        test_image = SimpleUploadedFile(
            "test_image.jpg",
            b"fake image content",
            content_type="image/jpeg"
        )
        
        client = Client()
        client.force_login(user)
        
        photo_response = client.post('/api/staff/checklist/photo/upload/', {
            'item_id': response.id,
            'photo': test_image
        }, HTTP_HOST='localhost:8000')
        
        assert photo_response.status_code == 200
        
        # Verify photo audit event
        photo_audit = AuditEvent.objects.filter(
            event_type='create',
            object_type='ChecklistPhoto'
        )
        assert photo_audit.exists()
    
    def test_checklist_performance(self):
        """Test checklist system performance with large datasets"""
        # Create user and profile
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        profile = UserProfile.objects.create(
            user=user,
            role='staff'
        )
        
        # Create many tasks
        tasks = []
        for i in range(50):
            task = Task.objects.create(
                title=f"Task {i}",
                task_type="cleaning",
                assigned_to=user
            )
            tasks.append(task)
        
        # Create template with many items
        template = ChecklistTemplate.objects.create(
            name="Performance Test Template",
            task_type="cleaning"
        )
        
        for i in range(20):
            ChecklistItem.objects.create(
                template=template,
                title=f"Item {i}"
            )
        
        # Assign checklists
        call_command('assign_checklists')
        
        # Verify all checklists were created
        assert TaskChecklist.objects.count() == 50
        
        # Verify all responses were created
        assert ChecklistResponse.objects.count() == 1000  # 50 tasks × 20 items
        
        # Test bulk operations performance
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/staff/checklist/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 50
