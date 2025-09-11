#!/usr/bin/env python
"""
Test the actual DRF ViewSet behavior for teststaff user
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend')

# Setup Django BEFORE importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from api.views import BookingViewSet
from api.permissions import DynamicBookingPermissions

def test_viewset_permissions():
    """Test the BookingViewSet permission behavior"""
    print("=== Testing BookingViewSet for teststaff ===\n")
    
    # Get the teststaff user
    try:
        user = User.objects.get(username='teststaff')
        print(f"✅ Found user: {user.username}")
    except User.DoesNotExist:
        print("❌ User 'teststaff' not found")
        return
    
    # Create a request factory
    factory = RequestFactory()
    
    # Create a GET request to the bookings endpoint
    request = factory.get('/api/bookings/')
    request.user = user
    
    # Create the ViewSet instance
    viewset = BookingViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    
    print("🔍 Testing ViewSet components:")
    
    # Test permission classes
    print(f"   📋 Permission classes: {viewset.permission_classes}")
    
    # Test get_permissions()
    permissions = viewset.get_permissions()
    print(f"   🔑 Permission instances: {permissions}")
    
    # Test each permission
    for perm in permissions:
        has_perm = perm.has_permission(request, viewset)
        print(f"      - {perm.__class__.__name__}: {has_perm}")
    
    # Test get_queryset()
    print(f"\n📊 Testing get_queryset():")
    try:
        queryset = viewset.get_queryset()
        count = queryset.count()
        print(f"   ✅ Queryset returned {count} bookings")
        
        # Show first few bookings
        if count > 0:
            for booking in queryset[:3]:
                print(f"      - Booking {booking.id}: {booking.guest_name} at {booking.property.name}")
    except Exception as e:
        print(f"   ❌ Error in get_queryset(): {e}")
    
    # Test action permissions
    print(f"\n🎬 Testing ViewSet actions:")
    
    # Test list action
    viewset.action = 'list'
    try:
        viewset.check_permissions(request)
        print(f"   ✅ List action: Permission granted")
    except Exception as e:
        print(f"   ❌ List action: Permission denied - {e}")
    
    # Test retrieve action
    viewset.action = 'retrieve'
    try:
        viewset.check_permissions(request)
        print(f"   ✅ Retrieve action: Permission granted")
    except Exception as e:
        print(f"   ❌ Retrieve action: Permission denied - {e}")

def test_permission_class_instantiation():
    """Test how DRF instantiates permission classes"""
    print(f"\n🏗️  Testing Permission Class Instantiation:")
    
    # Test direct instantiation
    try:
        perm1 = DynamicBookingPermissions()
        print(f"   ✅ Direct instantiation works: {perm1}")
        print(f"      Permission map: {perm1.permission_map}")
    except Exception as e:
        print(f"   ❌ Direct instantiation failed: {e}")
    
    # Test how DRF would instantiate it
    try:
        # This is how DRF instantiates permission classes
        perm_class = DynamicBookingPermissions
        perm_instance = perm_class()
        print(f"   ✅ DRF-style instantiation works: {perm_instance}")
        print(f"      Permission map: {perm_instance.permission_map}")
    except Exception as e:
        print(f"   ❌ DRF-style instantiation failed: {e}")

if __name__ == "__main__":
    test_permission_class_instantiation()
    test_viewset_permissions()
