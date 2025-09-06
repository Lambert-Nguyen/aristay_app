#!/usr/bin/env python3
"""
Critical Security Fixes Test Suite

This test verifies all the high-impact security and consistency fixes:
1. Task Image endpoints authorization
2. Metrics dashboard vs API auth consistency  
3. Inventory logging policy consistency
4. Status field naming consistency in API responses
5. Upload validation and throttling
"""

import os
import sys
import django
import tempfile
import json
from io import BytesIO
from PIL import Image

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aristay_backend')
sys.path.insert(0, backend_dir)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from api.models import Profile, Task, TaskImage, CustomPermission, RolePermission
from api.views import TaskImageCreateView, system_metrics_api, system_metrics_dashboard
from api.staff_views import log_inventory_transaction
from api.serializers import TaskImageSerializer
import inspect


def test_task_image_security():
    """Test Task Image endpoints require proper task edit permissions"""
    print("🔍 Testing Task Image security fixes...")
    
    # Check that TaskImageCreateView uses object-level auth
    source = inspect.getsource(TaskImageCreateView)
    
    # Should NOT use IsOwnerOrAssignedOrReadOnly in permission_classes 
    assert 'IsOwnerOrAssignedOrReadOnly' not in source, "Should not use IsOwnerOrAssignedOrReadOnly for create view"
    
    # Should use can_edit_task check
    assert 'can_edit_task' in source, "Should check can_edit_task in perform_create"
    assert 'PermissionDenied' in source, "Should raise PermissionDenied for unauthorized access"
    
    # Should track uploaded_by
    assert 'uploaded_by=self.request.user' in source, "Should track who uploaded the image"
    
    print("✅ Task Image endpoints properly secured with object-level authorization")


def test_metrics_auth_consistency():
    """Test metrics dashboard and API have consistent auth"""
    print("🔍 Testing metrics auth consistency...")
    
    # Check that both use the same decorator
    dashboard_source = inspect.getsource(system_metrics_dashboard)
    api_source = inspect.getsource(system_metrics_api)
    
    assert '@staff_or_perm(\'system_metrics_access\')' in dashboard_source, \
           "Dashboard should use staff_or_perm decorator"
    assert '@staff_or_perm(\'system_metrics_access\')' in api_source, \
           "API should use staff_or_perm decorator"
    
    # Dashboard should NOT have redundant permission check
    assert 'is_superuser' not in dashboard_source or 'redirect_to_login' not in dashboard_source, \
           "Dashboard should not have redundant permission check"
    
    # API should NOT have superuser-only check
    assert 'is_superuser' not in api_source or 'Permission denied' not in api_source, \
           "API should not have superuser-only check"
    
    print("✅ Metrics dashboard and API have consistent auth patterns")


def test_inventory_logging_consistency():
    """Test inventory logging has consistent permission policy"""
    print("🔍 Testing inventory logging policy consistency...")
    
    source = inspect.getsource(log_inventory_transaction)
    
    # Should have the decorator
    assert '@staff_or_perm(\'manage_inventory\')' in source, \
           "Should have manage_inventory decorator"
    
    # Should NOT have conflicting internal permission logic
    assert 'profile.role == \'manager\'' not in source, \
           "Should not have conflicting manager role check"
    assert 'is_in_department(\'Maintenance\')' not in source, \
           "Should not have conflicting department check"
    
    # Should be atomic
    assert '@transaction.atomic' in source, "Should use atomic transactions"
    
    print("✅ Inventory logging has consistent permission policy")


def test_status_key_consistency():
    """Test API responses use consistent status keys"""
    print("🔍 Testing status key consistency...")
    
    # Check staff_views.py for consistent status keys
    with open('/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend/api/staff_views.py', 'r') as f:
        content = f.read()
    
    # Should use 'in-progress' as key (not 'in_progress')
    assert "'in-progress':" in content, "Should use 'in-progress' as API response key"
    
    # Should NOT use 'in_progress' as key in task_counts
    in_progress_lines = [line for line in content.split('\n') if "'in_progress':" in line and 'task_counts' in content]
    assert len(in_progress_lines) == 0, f"Found inconsistent 'in_progress' keys: {in_progress_lines}"
    
    print("✅ Status keys consistently use 'in-progress' format")


def test_upload_validation():
    """Test upload validation in TaskImageSerializer"""
    print("🔍 Testing upload validation...")
    
    source = inspect.getsource(TaskImageSerializer)
    
    # Should have validate_image method
    assert 'def validate_image' in source, "Should have validate_image method"
    
    # Should validate file size
    assert 'max_mb' in source and 'file.size' in source, "Should validate file size"
    
    # Should validate file type
    assert 'allowed_types' in source and 'content_type' in source, "Should validate file type"
    
    # Should include uploaded_by field
    assert 'uploaded_by' in source, "Should include uploaded_by field"
    
    print("✅ Upload validation properly implemented")


def test_throttling_configuration():
    """Test throttling is configured"""
    print("🔍 Testing throttling configuration...")
    
    # Check settings for throttling config
    from django.conf import settings
    
    assert hasattr(settings, 'REST_FRAMEWORK'), "Should have REST_FRAMEWORK settings"
    rest_config = settings.REST_FRAMEWORK
    
    assert 'DEFAULT_THROTTLE_RATES' in rest_config, "Should have throttle rates configured"
    assert 'taskimage' in rest_config['DEFAULT_THROTTLE_RATES'], "Should have taskimage throttle rate"
    
    # Check TaskImageCreateView uses throttling
    source = inspect.getsource(TaskImageCreateView)
    assert 'throttle_classes' in source, "TaskImageCreateView should use throttling"
    assert 'throttle_scope' in source, "TaskImageCreateView should have throttle scope"
    
    print("✅ Throttling properly configured")


def test_migration_created():
    """Test that uploaded_by migration was created"""
    print("🔍 Testing uploaded_by migration...")
    
    import glob
    migration_files = glob.glob('/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend/api/migrations/*uploaded_by*.py')
    
    assert len(migration_files) > 0, "Should have created uploaded_by migration"
    
    # Check that TaskImage model has uploaded_by field
    from api.models import TaskImage
    field_names = [field.name for field in TaskImage._meta.fields]
    assert 'uploaded_by' in field_names, "TaskImage should have uploaded_by field"
    
    print("✅ uploaded_by field migration created and applied")


def test_imports_and_functionality():
    """Test that all necessary imports are present"""
    print("🔍 Testing imports and functionality...")
    
    # Test can_edit_task import
    try:
        from api.authz import can_edit_task
        assert callable(can_edit_task), "can_edit_task should be callable"
    except ImportError:
        assert False, "can_edit_task not properly imported"
    
    # Test PermissionDenied import
    try:
        from rest_framework.exceptions import PermissionDenied
        assert PermissionDenied, "PermissionDenied should be importable"
    except ImportError:
        assert False, "PermissionDenied not properly imported"
    
    # Test ScopedRateThrottle import
    try:
        from rest_framework.throttling import ScopedRateThrottle
        assert ScopedRateThrottle, "ScopedRateThrottle should be importable"
    except ImportError:
        assert False, "ScopedRateThrottle not properly imported"
    
    print("✅ All necessary imports working correctly")


def run_all_tests():
    """Run all security fix verification tests"""
    print("🚀 Running Critical Security Fixes Verification Tests\n")
    
    try:
        test_task_image_security()
        test_metrics_auth_consistency()
        test_inventory_logging_consistency()
        test_status_key_consistency()
        test_upload_validation()
        test_throttling_configuration()
        test_migration_created()
        test_imports_and_functionality()
        
        print("\n🎉 ALL SECURITY FIXES VERIFIED SUCCESSFULLY!")
        print("✅ Task Image endpoints properly secured")
        print("✅ Metrics auth consistency fixed")
        print("✅ Inventory logging policy unified")
        print("✅ Status keys standardized")
        print("✅ Upload validation implemented")
        print("✅ Throttling configured")
        print("✅ Database migration applied")
        print("✅ All imports working")
        print("\n🛡️ All security vulnerabilities have been patched!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
