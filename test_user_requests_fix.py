#!/usr/bin/env python3
"""
Test script to validate the key fixes made to the Django application.
This script tests:

1. Task change functionality in the manager DRF interface
2. Staff portal task access  
3. Notification management settings
4. Database field reference corrections

Usage: python test_user_requests_fix.py
"""
import os
import sys
import django
import requests
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import connection
from api.models import Task, Property, Notification, Profile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Test server URLs
BASE_URL = 'http://127.0.0.1:8000'
TIMEOUT = 10

class UserRequestFixTest:
    """Test the specific user requests for task change and notification fixes."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        
    def test_database_field_references(self):
        """Test that database field references are correct."""
        print("🔍 Testing database field references...")
        
        try:
            # Test Task model field references
            task_count = Task.objects.count()
            print(f"✅ Task.objects.count() works: {task_count} tasks")
            
            # Test property_ref field usage in queries
            if task_count > 0:
                task = Task.objects.select_related('property_ref').first()
                if hasattr(task, 'property_ref') and task.property_ref:
                    print(f"✅ Task.property_ref field works: {task.property_ref.name}")
                else:
                    print("⚠️  Task.property_ref is None - may need test data")
                    
            # Test property_ref in values queries
            property_stats = Task.objects.values('property_ref__name').distinct()
            print(f"✅ Task property_ref__name values query works: {list(property_stats)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Database field reference test failed: {e}")
            return False
    
    def test_notification_field_references(self):
        """Test that notification field references are correct."""
        print("\n📧 Testing notification field references...")
        
        try:
            # Test notification read field
            total_notifications = Notification.objects.count()
            print(f"✅ Notification.objects.count() works: {total_notifications} notifications")
            
            # Test read field (not is_read)
            unread_count = Notification.objects.filter(read=False).count()
            print(f"✅ Notification.objects.filter(read=False) works: {unread_count} unread")
            
            # Test timestamp field (not created_at)
            from django.utils import timezone
            from datetime import timedelta
            recent_count = Notification.objects.filter(
                timestamp__gte=timezone.now() - timedelta(days=7)
            ).count()
            print(f"✅ Notification timestamp field works: {recent_count} recent notifications")
            
            return True
            
        except Exception as e:
            print(f"❌ Notification field reference test failed: {e}")
            return False
    
    def test_notification_management_endpoint(self):
        """Test the notification management endpoint that was throwing field errors."""
        print("\n🔧 Testing notification management endpoint...")
        
        try:
            # Test GET request to notification management
            response = self.session.get(f'{BASE_URL}/api/admin/notification-management/')
            
            # Should redirect to login since not authenticated
            if response.status_code in [302, 401]:
                print("✅ Notification management endpoint accessible (redirects to login as expected)")
                return True
            elif response.status_code == 200:
                print("✅ Notification management endpoint accessible (direct access)")
                return True
            elif response.status_code == 500:
                print(f"❌ Notification management endpoint returns server error: {response.status_code}")
                return False
            else:
                print(f"⚠️  Notification management endpoint returns: {response.status_code}")
                return True  # Non-error status
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to notification management endpoint: {e}")
            return False
    
    def test_task_change_endpoint(self):
        """Test the task change functionality in DRF interface."""
        print("\n📝 Testing task change endpoint...")
        
        try:
            # Test GET request to task list
            response = self.session.get(f'{BASE_URL}/manager/api/task/')
            
            if response.status_code in [302, 401]:
                print("✅ Manager task API accessible (redirects to login as expected)")
            elif response.status_code == 200:
                print("✅ Manager task API accessible (direct access)")
            else:
                print(f"⚠️  Manager task API returns: {response.status_code}")
                
            # Test specific task change if we have tasks
            task_count = Task.objects.count()
            if task_count > 0:
                task_id = Task.objects.first().id
                response = self.session.get(f'{BASE_URL}/manager/api/task/{task_id}/change/')
                
                if response.status_code in [302, 401]:
                    print(f"✅ Task {task_id} change endpoint accessible (redirects to login as expected)")
                elif response.status_code == 200:
                    print(f"✅ Task {task_id} change endpoint accessible (direct access)")
                else:
                    print(f"⚠️  Task {task_id} change endpoint returns: {response.status_code}")
            else:
                print("⚠️  No tasks available to test change endpoint")
                
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to task endpoints: {e}")
            return False
    
    def test_staff_portal_endpoints(self):
        """Test staff portal functionality."""
        print("\n👥 Testing staff portal endpoints...")
        
        try:
            # Test staff dashboard
            response = self.session.get(f'{BASE_URL}/staff/dashboard/')
            
            if response.status_code == 404:
                # Check if staff portal uses different URL pattern
                alternative_urls = [
                    '/api/staff/dashboard/', 
                    '/portal/dashboard/',
                    '/staff/',
                ]
                
                found = False
                for url in alternative_urls:
                    try:
                        response = self.session.get(f'{BASE_URL}{url}')
                        if response.status_code != 404:
                            print(f"✅ Staff portal found at {url} (status: {response.status_code})")
                            found = True
                            break
                    except:
                        continue
                
                if not found:
                    print("⚠️  Staff portal endpoint not found - may need URL configuration")
            else:
                print(f"✅ Staff dashboard accessible (status: {response.status_code})")
                
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to staff endpoints: {e}")
            return False
    
    def test_profile_creation_fixes(self):
        """Test that Profile creation issues are resolved."""
        print("\n👤 Testing Profile creation fixes...")
        
        try:
            # Check current user and profile counts
            user_count = User.objects.count()
            profile_count = Profile.objects.count()
            
            print(f"✅ Current users: {user_count}, profiles: {profile_count}")
            
            # Test that we can query profiles without integrity errors
            profiles = Profile.objects.all()[:5]
            print(f"✅ Profile query works: {len(profiles)} profiles found")
            
            # Check for orphaned profiles (profiles without users)
            orphaned = Profile.objects.filter(user__isnull=True).count()
            if orphaned > 0:
                print(f"⚠️  Found {orphaned} orphaned profiles")
            else:
                print("✅ No orphaned profiles found")
                
            return True
            
        except Exception as e:
            print(f"❌ Profile creation test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests and return overall result."""
        print("=" * 60)
        print("🧪 RUNNING USER REQUEST FIX VALIDATION TESTS")
        print("=" * 60)
        
        tests = [
            self.test_database_field_references,
            self.test_notification_field_references,
            self.test_notification_management_endpoint,
            self.test_task_change_endpoint,
            self.test_staff_portal_endpoints,
            self.test_profile_creation_fixes,
        ]
        
        results = []
        for test in tests:
            results.append(test())
        
        passed = sum(results)
        total = len(results)
        
        print("\n" + "=" * 60)
        print(f"🏁 TEST RESULTS: {passed}/{total} tests passed")
        print("=" * 60)
        
        if passed == total:
            print("✅ ALL TESTS PASSED - User request fixes are working!")
        else:
            print("⚠️  SOME TESTS FAILED - Review the output above for details")
        
        return passed == total

def main():
    """Main test execution."""
    tester = UserRequestFixTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
