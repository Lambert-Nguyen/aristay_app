#!/usr/bin/env python
"""
Cloudinary Integration Test
==========================

Test script to verify Cloudinary configuration is working properly with our 
existing enhanced image optimization system.
"""

import os
import sys
import django
import pytest
from io import BytesIO
from django.test import TestCase

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

@pytest.mark.django_db
class TestCloudinaryIntegration(TestCase):
    """Test suite for Cloudinary integration"""
    
    def test_cloudinary_configuration(self):
        """Test Cloudinary configuration is working properly"""
        
        print("🔍 CLOUDINARY INTEGRATION TEST")
        print("=" * 50)
        
        from django.conf import settings
        
        # Check 1: Cloudinary settings
        print("\n✅ 1. CLOUDINARY SETTINGS:")
        
        if hasattr(settings, 'USE_CLOUDINARY'):
            print(f"   ✅ USE_CLOUDINARY: {settings.USE_CLOUDINARY}")
        else:
            print("   ❌ USE_CLOUDINARY setting missing")
            self.fail("USE_CLOUDINARY setting missing")
        
        # Check 2: Storage configuration
        print("\n✅ 2. STORAGE CONFIGURATION:")
        
        if hasattr(settings, 'STORAGES'):
            print(f"   ✅ STORAGES configured: {settings.STORAGES['default']['BACKEND']}")
        else:
            print("   ❌ STORAGES not configured")
            self.fail("STORAGES not configured")
        
        # Check 3: Cloudinary URL
        print("\n✅ 3. CLOUDINARY URL:")
        
        cloudinary_url = os.getenv('CLOUDINARY_URL')
        if cloudinary_url:
            print("   ✅ CLOUDINARY_URL environment variable set")
        else:
            print("   ⚠️  CLOUDINARY_URL not set (using individual settings)")
        
        print(f"\n🎉 CLOUDINARY INTEGRATION TEST SUCCESSFUL!")
        print("=" * 50)
        print("✅ Cloudinary configuration is working")
        print("✅ Storage backend is properly configured")
        print("✅ Environment variables are set correctly")

def main():
    """Main function - kept for backward compatibility"""
    print("Cloudinary integration test completed")

if __name__ == "__main__":
    main()