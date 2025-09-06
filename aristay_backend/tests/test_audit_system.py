"""
Test Agent's Phase 2: Structured Audit System
Comprehensive validation of audit event capture and API functionality
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
from rest_framework.test import APITestCase
from rest_framework import status
from api.models import Property, Task, AuditEvent
from api.audit_signals import set_audit_context, get_audit_context, clear_audit_context
from api.audit_middleware import AuditMiddleware
from unittest.mock import Mock

User = get_user_model()


class AuditSystemTestCase(TestCase):
    """Test the audit system functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )
        
        self.property = Property.objects.create(
            name='Test Property Audit',
            address='123 Audit St',
            created_by=self.user
        )
    
    def test_audit_context_management(self):
        """Test audit context setting and retrieval."""
        # Test setting context
        set_audit_context(
            user=self.user,
            request_id='test-123',
            ip_address='192.168.1.1',
            user_agent='Test Agent'
        )
        
        context = get_audit_context()
        
        self.assertEqual(context['user'], self.user)
        self.assertEqual(context['request_id'], 'test-123')
        self.assertEqual(context['ip_address'], '192.168.1.1')
        self.assertEqual(context['user_agent'], 'Test Agent')
        
        # Test clearing context
        clear_audit_context()
        context = get_audit_context()
        
        self.assertIsNone(context['user'])
        self.assertIsNone(context['ip_address'])
        self.assertEqual(context['user_agent'], '')
        # request_id should still be generated
        self.assertIsNotNone(context['request_id'])
    
    def test_audit_middleware(self):
        """Test audit middleware sets context correctly."""
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        request.META['HTTP_USER_AGENT'] = 'Test Browser'
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        middleware = AuditMiddleware()
        
        # Process request
        result = middleware.process_request(request)
        self.assertIsNone(result)  # Middleware should return None
        
        # Check context was set
        context = get_audit_context()
        self.assertEqual(context['user'], self.user)
        self.assertEqual(context['ip_address'], '127.0.0.1')
        self.assertEqual(context['user_agent'], 'Test Browser')
        
        # Process response should clear context
        response = Mock()
        middleware.process_response(request, response)
        
        # Context should be cleared
        context = get_audit_context()
        self.assertIsNone(context['user'])
    
    def test_property_creation_audit(self):
        """Test that property creation generates audit events."""
        # Set audit context
        set_audit_context(
            user=self.user,
            request_id='create-test-123',
            ip_address='192.168.1.100'
        )
        
        initial_count = AuditEvent.objects.count()
        
        # Create a new property
        new_property = Property.objects.create(
            name='Audited Property',
            address='456 Audit Ave',
            created_by=self.user
        )
        
        # Check audit event was created
        self.assertEqual(AuditEvent.objects.count(), initial_count + 1)
        
        audit_event = AuditEvent.objects.latest('created_at')
        self.assertEqual(audit_event.object_type, 'Property')
        self.assertEqual(audit_event.object_id, str(new_property.pk))
        self.assertEqual(audit_event.action, 'create')
        self.assertEqual(audit_event.actor, self.user)
        self.assertEqual(audit_event.request_id, 'create-test-123')
        self.assertEqual(audit_event.ip_address, '192.168.1.100')
        
        # Check changes field
        self.assertIn('action', audit_event.changes)
        self.assertEqual(audit_event.changes['action'], 'create')
        self.assertIn('new_values', audit_event.changes)
        self.assertIn('name', audit_event.changes['new_values'])
        self.assertEqual(audit_event.changes['new_values']['name'], 'Audited Property')
    
    def test_property_update_audit(self):
        """Test that property updates generate audit events."""
        set_audit_context(user=self.user, request_id='update-test-123')
        
        initial_count = AuditEvent.objects.count()
        
        # Update the property
        self.property.name = 'Updated Property Name'
        self.property.save()
        
        # Check audit event was created
        self.assertEqual(AuditEvent.objects.count(), initial_count + 1)
        
        audit_event = AuditEvent.objects.latest('created_at')
        self.assertEqual(audit_event.object_type, 'Property')
        self.assertEqual(audit_event.object_id, str(self.property.pk))
        self.assertEqual(audit_event.action, 'update')
        self.assertEqual(audit_event.actor, self.user)
        
        # Check changes field shows the update
        self.assertIn('fields_changed', audit_event.changes)
        self.assertIn('name', audit_event.changes['fields_changed'])
        self.assertIn('old_values', audit_event.changes)
        self.assertIn('new_values', audit_event.changes)
        self.assertEqual(audit_event.changes['old_values']['name'], 'Test Property Audit')
        self.assertEqual(audit_event.changes['new_values']['name'], 'Updated Property Name')
    
    def test_property_deletion_audit(self):
        """Test that property deletion generates audit events."""
        set_audit_context(user=self.user, request_id='delete-test-123')
        
        property_id = self.property.pk
        initial_count = AuditEvent.objects.count()
        
        # Delete the property
        self.property.delete()
        
        # Check audit event was created
        self.assertEqual(AuditEvent.objects.count(), initial_count + 1)
        
        audit_event = AuditEvent.objects.latest('created_at')
        self.assertEqual(audit_event.object_type, 'Property')
        self.assertEqual(audit_event.object_id, str(property_id))
        self.assertEqual(audit_event.action, 'delete')
        self.assertEqual(audit_event.actor, self.user)
        
        # Check changes field shows deletion info
        self.assertIn('deleted_object', audit_event.changes)
        self.assertIn('id', audit_event.changes['deleted_object'])
        self.assertEqual(audit_event.changes['deleted_object']['id'], property_id)
    
    def test_task_creation_with_agent_validations(self):
        """Test task creation with agent's validation features."""
        set_audit_context(user=self.user, request_id='task-test-123')
        
        initial_count = AuditEvent.objects.count()
        
        # Create task with agent's enhanced features
        task = Task.objects.create(
            title='Test Audit Task',
            description='Testing audit system',
            property=self.property,
            status='pending',
            is_locked_by_user=True,  # Agent's lock mechanism
            created_by=self.user
        )
        
        # Check audit event was created
        self.assertEqual(AuditEvent.objects.count(), initial_count + 1)
        
        audit_event = AuditEvent.objects.latest('created_at')
        self.assertEqual(audit_event.object_type, 'Task')
        self.assertEqual(audit_event.action, 'create')
        
        # Verify agent's lock field is captured
        self.assertIn('is_locked_by_user', audit_event.changes['new_values'])
        self.assertTrue(audit_event.changes['new_values']['is_locked_by_user'])


class AuditAPITestCase(APITestCase):
    """Test the audit API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='api_test_user',
            email='api@example.com',
            password='testpass123'
        )
        
        self.staff_user = User.objects.create_user(
            username='staff_user',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create some audit events
        self.audit_event1 = AuditEvent.objects.create(
            object_type='Property',
            object_id='1',
            action='create',
            actor=self.user,
            changes={'action': 'create', 'new_values': {'name': 'Test Property'}},
            request_id='test-request-1',
            ip_address='192.168.1.1'
        )
        
        self.audit_event2 = AuditEvent.objects.create(
            object_type='Task',
            object_id='1',
            action='update',
            actor=self.staff_user,
            changes={'action': 'update', 'fields_changed': ['status']},
            request_id='test-request-2',
            ip_address='192.168.1.2'
        )
    
    def test_audit_list_requires_authentication(self):
        """Test that audit list requires authentication."""
        response = self.client.get('/api/audit-events/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_audit_list_for_regular_user(self):
        """Test audit list for regular user shows only their events."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/audit-events/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['actor'], self.user.pk)
    
    def test_audit_list_for_staff_user(self):
        """Test audit list for staff user shows all events."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/audit-events/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_audit_filtering(self):
        """Test audit event filtering."""
        self.client.force_authenticate(user=self.staff_user)
        
        # Filter by object type
        response = self.client.get('/api/audit-events/?object_type=Property')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['object_type'], 'Property')
        
        # Filter by action
        response = self.client.get('/api/audit-events/?action=update')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['action'], 'update')
    
    def test_audit_search(self):
        """Test audit event search functionality."""
        self.client.force_authenticate(user=self.staff_user)
        
        # Search by object type
        response = self.client.get('/api/audit-events/?search=Property')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Search by actor username
        response = self.client.get('/api/audit-events/?search=staff_user')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_audit_export(self):
        """Test audit event CSV export."""
        self.client.force_authenticate(user=self.staff_user)
        
        response = self.client.get('/api/audit-events/export/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename=', response['Content-Disposition'])
        
        # Check CSV content
        content = response.content.decode('utf-8')
        self.assertIn('Created At,Action,Object Type', content)
        self.assertIn('Property', content)
        self.assertIn('Task', content)
    
    def test_audit_summary(self):
        """Test audit summary endpoint."""
        self.client.force_authenticate(user=self.staff_user)
        
        response = self.client.get('/api/audit-events/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('total_events', data)
        self.assertIn('action_breakdown', data)
        self.assertIn('top_object_types', data)
        self.assertIn('top_actors', data)
        
        self.assertEqual(data['total_events'], 2)
        self.assertEqual(data['action_breakdown']['create'], 1)
        self.assertEqual(data['action_breakdown']['update'], 1)
    
    def test_audit_related_events(self):
        """Test finding related audit events."""
        self.client.force_authenticate(user=self.staff_user)
        
        response = self.client.get(f'/api/audit-events/{self.audit_event1.pk}/related_events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return empty since we only have one event per object
        self.assertEqual(len(response.data), 0)
    
    def test_audit_readonly_operations(self):
        """Test that audit events are read-only."""
        self.client.force_authenticate(user=self.staff_user)
        
        # Try to create (should fail)
        response = self.client.post('/api/audit-events/', {
            'object_type': 'TestModel',
            'object_id': '999',
            'action': 'create'
        })
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try to update (should fail)
        response = self.client.put(f'/api/audit-events/{self.audit_event1.pk}/', {
            'object_type': 'Modified'
        })
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try to delete (should fail)
        response = self.client.delete(f'/api/audit-events/{self.audit_event1.pk}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AuditIntegrationTestCase(TestCase):
    """Integration tests for the complete audit system."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='integration_user',
            email='integration@example.com',
            password='testpass123'
        )
    
    def test_complete_audit_workflow(self):
        """Test complete audit workflow from creation to API access."""
        # Simulate request with middleware
        set_audit_context(
            user=self.user,
            request_id='workflow-test-123',
            ip_address='10.0.0.1',
            user_agent='Integration Test Agent'
        )
        
        initial_count = AuditEvent.objects.count()
        
        # 1. Create a property (should generate create audit)
        property_obj = Property.objects.create(
            name='Integration Test Property',
            address='789 Integration Blvd',
            created_by=self.user
        )
        
        # 2. Update the property (should generate update audit)
        property_obj.name = 'Updated Integration Property'
        property_obj.save()
        
        # 3. Create a task linked to the property (should generate create audit)
        task = Task.objects.create(
            title='Integration Test Task',
            description='Testing full audit integration',
            property=property_obj,
            status='pending',
            created_by=self.user
        )
        
        # 4. Update task with agent's lock feature (should generate update audit)
        task.is_locked_by_user = True
        task.status = 'in-progress'
        task.save()
        
        # 5. Delete the task (should generate delete audit)
        task.delete()
        
        # Verify all audit events were created
        final_count = AuditEvent.objects.count()
        self.assertEqual(final_count, initial_count + 5)  # 5 operations
        
        # Verify the events in sequence
        events = AuditEvent.objects.filter(
            request_id='workflow-test-123'
        ).order_by('created_at')
        
        # Property creation
        self.assertEqual(events[0].object_type, 'Property')
        self.assertEqual(events[0].action, 'create')
        self.assertEqual(events[0].actor, self.user)
        
        # Property update
        self.assertEqual(events[1].object_type, 'Property')
        self.assertEqual(events[1].action, 'update')
        self.assertIn('name', events[1].changes['fields_changed'])
        
        # Task creation
        self.assertEqual(events[2].object_type, 'Task')
        self.assertEqual(events[2].action, 'create')
        
        # Task update with agent features
        self.assertEqual(events[3].object_type, 'Task')
        self.assertEqual(events[3].action, 'update')
        self.assertIn('is_locked_by_user', events[3].changes['fields_changed'])
        self.assertIn('status', events[3].changes['fields_changed'])
        
        # Task deletion
        self.assertEqual(events[4].object_type, 'Task')
        self.assertEqual(events[4].action, 'delete')
        
        # Verify all events have correct context
        for event in events:
            self.assertEqual(event.request_id, 'workflow-test-123')
            self.assertEqual(event.ip_address, '10.0.0.1')
            self.assertEqual(event.user_agent, 'Integration Test Agent')
            self.assertEqual(event.actor, self.user)
