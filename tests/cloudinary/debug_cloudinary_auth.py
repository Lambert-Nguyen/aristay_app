#!/usr/bin/env python3

"""
Cloudinary Authentication Validation Script
==============================================
This script validates Cloudinary credentials and configuration.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

import cloudinary
from django.conf import settings

def main():
    print("🔧 Cloudinary Authentication Debug")
    print("=" * 50)
    
    # Print environment variable
    cloudinary_url = os.getenv('CLOUDINARY_URL')
    print(f"CLOUDINARY_URL from .env: {cloudinary_url}")
    
    # Print parsed configuration
    import cloudinary as cl
    config = cl.config()
    print(f"Cloudinary config:")
    print(f"  - Cloud name: {config.cloud_name}")
    print(f"  - API key: {config.api_key}")
    print(f"  - API secret: {config.api_secret[:5]}...{config.api_secret[-5:] if config.api_secret else 'None'}")
    
    # Test a simple API call
    print("\n🧪 Testing Cloudinary API connection...")
    try:
        import cloudinary.api
        # Try to get account details (this doesn't upload anything)
        result = cloudinary.api.ping()
        print("✅ Cloudinary API connection successful!")
        print(f"   Status: {result.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ Cloudinary API connection failed: {e}")
        
        # Additional debugging
        print("\n🔍 Debugging info:")
        print(f"   - CLOUDINARY_URL format should be: cloudinary://api_key:api_secret@cloud_name")
        print(f"   - Your URL format: cloudinary://{cloudinary.config().api_key}:{cloudinary.config().api_secret}@{cloudinary.config().cloud_name}")
        
        # Check if the URL is being parsed correctly
        if cloudinary_url:
            parts = cloudinary_url.replace('cloudinary://', '').split('@')
            if len(parts) == 2:
                auth_part = parts[0]
                cloud_name_part = parts[1]
                if ':' in auth_part:
                    api_key_part, api_secret_part = auth_part.split(':', 1)
                    print(f"   - Parsed API key: {api_key_part}")
                    print(f"   - Parsed API secret: {api_secret_part[:5]}...{api_secret_part[-5:]}")
                    print(f"   - Parsed cloud name: {cloud_name_part}")
                else:
                    print("   - ❌ No ':' found in auth part")
            else:
                print("   - ❌ Invalid CLOUDINARY_URL format")
        
    print("\n✅ Debug completed")

if __name__ == '__main__':
    main()
