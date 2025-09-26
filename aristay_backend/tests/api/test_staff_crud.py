"""
Test CRUD operations for staff tasks portal.
"""

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from api.models import Task, Property, Profile


@override_settings(
    AUTHENTICATION_BACKENDS=[
        'django.contrib.auth.backends.ModelBackend',
    ]
)
class StaffTasksCRUDTestCase(TestCase):
    """Test CRUD operations for staff tasks portal."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user and profile
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.profile, created = Profile.objects.get_or_create(
            user=self.user,
            defaults={
                'role': 'manager',
                'timezone': 'America/New_York'
            }
        )
        
        # Ensure the profile has the manager role
        if not created:
            self.profile.role = 'manager'
            self.profile.save()
        
        # Create test property
        self.property_obj = Property.objects.create(
            name='Test Property',
            address='123 Test St, Test City, FL 12345'
        )
        
        # Create test client
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_tasks_list_access(self):
        """Test that tasks list is accessible."""
        response = self.client.get('/api/staff/tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Tasks')
    
    def test_task_creation_form_access(self):
        """Test that task creation form is accessible."""
        response = self.client.get('/api/staff/tasks/create/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create New Task')
    
    def test_task_creation(self):
        """Test task creation."""
        task_data = {
            'title': 'Test Task',
            'description': 'This is a test task',
            'task_type': 'cleaning',
            'status': 'pending',
            'assigned_to': self.user.id,
            'property_ref': self.property_obj.id,
            'due_date': '2024-12-31T09:00'
        }
        
        response = self.client.post('/api/staff/tasks/create/', task_data)
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        
        # Check if task was created
        task = Task.objects.filter(title='Test Task').first()
        self.assertIsNotNone(task)
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.task_type, 'cleaning')
        self.assertEqual(task.status, 'pending')
    
    def test_task_detail_access(self):
        """Test task detail view."""
        # Create a task first
        task = Task.objects.create(
            title='Test Task',
            description='Test description',
            task_type='cleaning',
            status='pending',
            assigned_to=self.user,
            property_ref=self.property_obj,
            created_by=self.user
        )
        
        response = self.client.get(f'/api/staff/tasks/{task.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Task')
    
    def test_task_edit_form_access(self):
        """Test task edit form access."""
        # Create a task first
        task = Task.objects.create(
            title='Test Task',
            description='Test description',
            task_type='cleaning',
            status='pending',
            assigned_to=self.user,
            property_ref=self.property_obj,
            created_by=self.user
        )
        
        response = self.client.get(f'/api/staff/tasks/{task.id}/edit/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Task: Test Task')
    
    def test_task_update(self):
        """Test task update."""
        # Create a task first
        task = Task.objects.create(
            title='Test Task',
            description='Test description',
            task_type='cleaning',
            status='pending',
            assigned_to=self.user,
            property_ref=self.property_obj,
            created_by=self.user
        )
        
        update_data = {
            'title': 'Updated Test Task',
            'description': 'This is an updated test task',
            'task_type': 'cleaning',
            'status': 'in-progress',
            'assigned_to': self.user.id,
            'property_ref': self.property_obj.id,
            'due_date': '2024-12-31T10:00'
        }
        
        response = self.client.post(f'/api/staff/tasks/{task.id}/edit/', update_data)
        self.assertEqual(response.status_code, 302)  # Redirect after update
        
        # Check if task was updated
        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated Test Task')
        self.assertEqual(task.status, 'in-progress')
    
    def test_task_duplication(self):
        """Test task duplication."""
        # Create a task first
        task = Task.objects.create(
            title='Test Task',
            description='Test description',
            task_type='cleaning',
            status='pending',
            assigned_to=self.user,
            property_ref=self.property_obj,
            created_by=self.user
        )
        
        response = self.client.get(f'/api/staff/tasks/{task.id}/duplicate/')
        self.assertEqual(response.status_code, 302)  # Redirect after duplication
        
        # Check if duplicate was created
        duplicate_task = Task.objects.filter(title='Test Task (Copy)').first()
        self.assertIsNotNone(duplicate_task)
        self.assertEqual(duplicate_task.task_type, 'cleaning')
        self.assertEqual(duplicate_task.status, 'pending')
    
    def test_task_deletion(self):
        """Test task deletion."""
        # Create a task first
        task = Task.objects.create(
            title='Test Task',
            description='Test description',
            task_type='cleaning',
            status='pending',
            assigned_to=self.user,
            property_ref=self.property_obj,
            created_by=self.user
        )
        
        task_id = task.id
        response = self.client.post(f'/api/staff/tasks/{task_id}/delete/')
        self.assertEqual(response.status_code, 302)  # Redirect after deletion
        
        # Check if task was deleted
        self.assertFalse(Task.objects.filter(id=task_id).exists())
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access CRUD operations."""
        # Create a regular user without manager role
        regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='testpass123'
        )
        
        Profile.objects.get_or_create(
            user=regular_user,
            defaults={
                'role': 'staff',
                'timezone': 'America/New_York'
            }
        )
        
        # Login as regular user
        self.client.force_login(regular_user)
        
        # Try to access task creation (should be denied for staff without permission)
        response = self.client.get('/api/staff/tasks/create/')
        self.assertEqual(response.status_code, 302)  # Staff without permission redirected
        
        # Create a task as regular user
        task = Task.objects.create(
            title='Regular User Task',
            description='Test description',
            task_type='cleaning',
            status='pending',
            assigned_to=regular_user,
            property_ref=self.property_obj,
            created_by=regular_user
        )
        
        # Try to edit the task (should be allowed for creator)
        response = self.client.get(f'/api/staff/tasks/{task.id}/edit/')
        self.assertEqual(response.status_code, 200)
        
        # Try to delete the task (should be allowed for creator)
        response = self.client.post(f'/api/staff/tasks/{task.id}/delete/')
        self.assertEqual(response.status_code, 302)
