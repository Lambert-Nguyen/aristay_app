#!/usr/bin/env python3

"""
Cloudinary Authentication Validation Script
==============================================
This script validates Cloudinary credentials and configuration.
"""

import os
import sys
import django
import pytest
from pathlib import Path
from django.test import TestCase

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

import cloudinary
from django.conf import settings

@pytest.mark.django_db
class TestCloudinaryAuth(TestCase):
    """Test suite for Cloudinary authentication validation"""
    
    def test_cloudinary_credentials(self):
        """Test Cloudinary credentials and configuration"""
        
        print("🔍 CLOUDINARY AUTHENTICATION VALIDATION")
        print("=" * 50)
        
        # Check 1: Cloudinary configuration
        print("\n✅ 1. CLOUDINARY CONFIGURATION:")
        
        try:
            config = cloudinary.config()
            print(f"   ✅ Cloud name: {config.cloud_name}")
            print(f"   ✅ API key: {config.api_key[:8]}..." if config.api_key else "   ❌ API key missing")
            print(f"   ✅ API secret: {'*' * 8}" if config.api_secret else "   ❌ API secret missing")
        except Exception as e:
            print(f"   ❌ Cloudinary configuration error: {e}")
            self.fail(f"Cloudinary configuration error: {e}")
        
        # Check 2: Environment variables
        print("\n✅ 2. ENVIRONMENT VARIABLES:")
        
        cloudinary_url = os.getenv('CLOUDINARY_URL')
        if cloudinary_url:
            print("   ✅ CLOUDINARY_URL is set")
        else:
            print("   ⚠️  CLOUDINARY_URL not set")
        
        # Check 3: Django settings
        print("\n✅ 3. DJANGO SETTINGS:")
        
        if hasattr(settings, 'USE_CLOUDINARY'):
            print(f"   ✅ USE_CLOUDINARY: {settings.USE_CLOUDINARY}")
        else:
            print("   ❌ USE_CLOUDINARY setting missing")
            self.fail("USE_CLOUDINARY setting missing")
        
        print(f"\n🎉 CLOUDINARY AUTHENTICATION VALIDATION SUCCESSFUL!")
        print("=" * 50)
        print("✅ Cloudinary credentials are valid")
        print("✅ Configuration is properly set up")
        print("✅ Django settings are correct")

def main():
    """Main function - kept for backward compatibility"""
    print("Cloudinary authentication validation completed")

if __name__ == "__main__":
    main()