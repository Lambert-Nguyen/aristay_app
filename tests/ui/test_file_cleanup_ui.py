"""
Test File Cleanup UI functionality
"""
import json
import pytest
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

User = get_user_model()


@override_settings(
    AUTHENTICATION_BACKENDS=[
        'django.contrib.auth.backends.ModelBackend',
    ]
)
class FileCleanupUITestCase(TestCase):
    """Test cases for File Cleanup UI and API integration"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test users with different permission levels
        self.superuser = User.objects.create_superuser(
            'admin', 'admin@test.com', 'password123'
        )
        
        self.staff_user = User.objects.create_user(
            'staff', 'staff@test.com', 'password123'
        )
        
        self.regular_user = User.objects.create_user(
            'user', 'user@test.com', 'password123'
        )
        
        # URLs
        self.cleanup_page_url = reverse('admin-file-cleanup')
        self.cleanup_api_url = reverse('file-cleanup-api')
    
    def test_file_cleanup_page_requires_authentication(self):
        """Test that file cleanup page requires authentication"""
        response = self.client.get(self.cleanup_page_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/login/', response.url)
    
    def test_file_cleanup_page_requires_proper_permissions(self):
        """Test that file cleanup page requires manage_files permission or staff status"""
        # Regular user should be denied
        self.client.login(username='user', password='password123')
        response = self.client.get(self.cleanup_page_url)
        self.assertEqual(response.status_code, 403)
    
    def test_staff_user_can_access_file_cleanup_page(self):
        """Test that staff users can access file cleanup page"""
        self.client.login(username='staff', password='password123')
        response = self.client.get(self.cleanup_page_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'File Cleanup Management')
        self.assertContains(response, 'Storage Statistics')
        self.assertContains(response, 'Smart Suggestions')
        self.assertContains(response, 'Preview Cleanup')
        self.assertContains(response, 'Perform Cleanup')
    
    def test_superuser_can_access_file_cleanup_page(self):
        """Test that superusers can access file cleanup page"""
        self.client.login(username='admin', password='password123')
        response = self.client.get(self.cleanup_page_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'File Cleanup Management')
    
    def test_file_cleanup_api_requires_authentication(self):
        """Test that file cleanup API requires authentication"""
        response = self.client.get(self.cleanup_api_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_file_cleanup_api_requires_proper_permissions(self):
        """Test that file cleanup API requires manage_files permission or staff status"""
        # Regular user should be denied
        self.client.login(username='user', password='password123')
        response = self.client.get(self.cleanup_api_url)
        self.assertEqual(response.status_code, 403)
    
    @patch('api.services.file_cleanup_service.ImportFileCleanupService.get_storage_stats')
    def test_storage_stats_api_get(self, mock_get_stats):
        """Test GET request to storage stats API"""
        # Mock the service response
        mock_stats = {
            'total_files': 5,
            'total_size_mb': 150.5,
            'total_size_gb': 0.15,
            'oldest_file': '2024-01-01',
            'newest_file': '2024-03-01',
            'age_span_days': 60
        }
        mock_get_stats.return_value = mock_stats
        
        self.client.login(username='admin', password='password123')
        response = self.client.get(self.cleanup_api_url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['stats'], mock_stats)
    
    @patch('api.services.file_cleanup_service.ImportFileCleanupService.get_storage_stats')
    def test_storage_stats_api_post(self, mock_get_stats):
        """Test POST request for storage stats action"""
        # Mock the service response
        mock_stats = {
            'total_files': 3,
            'total_size_mb': 75.2,
            'total_size_gb': 0.07,
            'oldest_file': '2024-02-01',
            'newest_file': '2024-03-01',
            'age_span_days': 30
        }
        mock_get_stats.return_value = mock_stats
        
        self.client.login(username='admin', password='password123')
        response = self.client.post(
            self.cleanup_api_url,
            data=json.dumps({'action': 'stats'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['action'], 'stats')
        self.assertEqual(data['stats'], mock_stats)
    
    @patch('api.services.file_cleanup_service.ImportFileCleanupService.suggest_cleanup')
    def test_suggest_cleanup_api(self, mock_suggest):
        """Test suggest cleanup API action"""
        # Mock the service response
        mock_suggestion = {
            'current_size_mb': 200,
            'target_size_mb': 100,
            'action_needed': True,
            'recommended_days_to_keep': 30,
            'files_to_delete': 10,
            'space_to_free_mb': 120,
            'projected_final_size_mb': 80,
            'message': 'Keep last 30 days of files to reach target size'
        }
        mock_suggest.return_value = mock_suggestion
        
        self.client.login(username='admin', password='password123')
        response = self.client.post(
            self.cleanup_api_url,
            data=json.dumps({'action': 'suggest', 'target_mb': 100}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['action'], 'suggest')
        self.assertEqual(data['suggestion'], mock_suggestion)
    
    @patch('api.services.file_cleanup_service.ImportFileCleanupService.cleanup_old_files')
    def test_dry_run_cleanup_api(self, mock_cleanup):
        """Test dry run cleanup API action"""
        # Mock the service response
        mock_result = {
            'files_found': 8,
            'total_size_bytes': 157286400,  # ~150MB
            'total_size_mb': 150.0,
            'cutoff_date': '2024-01-01',
            'days_to_keep': 30,
            'dry_run': True
        }
        mock_cleanup.return_value = mock_result
        
        self.client.login(username='admin', password='password123')
        response = self.client.post(
            self.cleanup_api_url,
            data=json.dumps({'action': 'dry_run', 'days': 30}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['action'], 'dry_run')
        self.assertEqual(data['result'], mock_result)
        
        # Verify the service was called with correct parameters
        mock_cleanup.assert_called_once_with(30, True)  # days=30, dry_run=True
    
    @patch('api.services.file_cleanup_service.ImportFileCleanupService.cleanup_old_files')
    def test_actual_cleanup_api(self, mock_cleanup):
        """Test actual cleanup API action"""
        # Mock the service response
        mock_result = {
            'files_found': 8,
            'files_deleted': 8,
            'total_size_bytes': 157286400,
            'total_size_mb': 150.0,
            'space_freed_bytes': 157286400,
            'space_freed_mb': 150.0,
            'cutoff_date': '2024-01-01',
            'days_to_keep': 30,
            'dry_run': False,
            'errors': []
        }
        mock_cleanup.return_value = mock_result
        
        self.client.login(username='admin', password='password123')
        response = self.client.post(
            self.cleanup_api_url,
            data=json.dumps({'action': 'cleanup', 'days': 30}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['action'], 'cleanup')
        self.assertEqual(data['result'], mock_result)
        
        # Verify the service was called with correct parameters
        mock_cleanup.assert_called_once_with(30, False)  # days=30, dry_run=False
    
    def test_invalid_action_api(self):
        """Test API with invalid action"""
        self.client.login(username='admin', password='password123')
        response = self.client.post(
            self.cleanup_api_url,
            data=json.dumps({'action': 'invalid_action'}),
            content_type='application/json'
        )
        
        # Should return 400 status for invalid action
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Unknown action', data['error'])
    
    def test_malformed_json_api(self):
        """Test API with malformed JSON"""
        self.client.login(username='admin', password='password123')
        response = self.client.post(
            self.cleanup_api_url,
            data='invalid json',
            content_type='application/json'
        )
        
        # Should handle malformed JSON gracefully
        self.assertEqual(response.status_code, 200)
        # Should fall back to POST data parsing
    
    def test_file_cleanup_page_template_context(self):
        """Test that file cleanup page has correct template context"""
        self.client.login(username='admin', password='password123')
        response = self.client.get(self.cleanup_page_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['title'], 'Excel Import File Cleanup')
        self.assertEqual(response.context['user'], self.superuser)
    
    def test_csrf_token_in_template(self):
        """Test that CSRF token is included in the template"""
        self.client.login(username='admin', password='password123')
        response = self.client.get(self.cleanup_page_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'csrfmiddlewaretoken')
        # Check that the JavaScript file is loaded
        self.assertContains(response, 'file_cleanup.js')
    
    def test_http_methods_allowed(self):
        """Test that only GET and POST methods are allowed on API"""
        self.client.login(username='admin', password='password123')
        
        # GET should work
        response = self.client.get(self.cleanup_api_url)
        self.assertNotEqual(response.status_code, 405)
        
        # POST should work  
        response = self.client.post(self.cleanup_api_url, data='{}', content_type='application/json')
        self.assertNotEqual(response.status_code, 405)
        
        # Other methods should be rejected
        response = self.client.put(self.cleanup_api_url)
        self.assertEqual(response.status_code, 405)
        
        response = self.client.delete(self.cleanup_api_url)
        self.assertEqual(response.status_code, 405)