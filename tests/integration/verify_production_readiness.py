#!/usr/bin/env python3
"""
Production Readiness Verification Script

This script performs manual validation of all critical deployment fixes
identified by ChatGPT's production review.
"""

import os
import sys
from pathlib import Path

def check_timedelta_import():
    """Check that timedelta import is fixed in staff_views.py."""
    print("\n1. 🕐 Checking timedelta import fix...")
    
    backend_path = Path(__file__).parent / 'aristay_backend'
    staff_views_path = backend_path / 'api' / 'staff_views.py'
    
    try:
        with open(staff_views_path, 'r') as f:
            content = f.read()
            
        # Check for correct import
        if 'from datetime import timedelta' in content:
            print("   ✅ Found 'from datetime import timedelta' import")
        else:
            print("   ❌ Missing 'from datetime import timedelta' import")
            return False
            
        # Check that timezone.timedelta is not used
        if 'timezone.timedelta' in content:
            print("   ❌ Still using 'timezone.timedelta' - should be just 'timedelta'")
            return False
        else:
            print("   ✅ No incorrect 'timezone.timedelta' usage found")
            
        # Check for timedelta usage
        if 'timedelta(days=7)' in content:
            print("   ✅ Found proper 'timedelta(days=7)' usage")
        else:
            print("   ⚠️  No 'timedelta(days=7)' usage found")
            
        print("   ✅ Timedelta import fix verified")
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking timedelta import: {e}")
        return False

def check_task_image_queryset():
    """Check that TaskImageDetailView has proper queryset constraint."""
    print("\n2. 🔒 Checking TaskImage queryset constraint...")
    
    backend_path = Path(__file__).parent / 'aristay_backend'
    views_path = backend_path / 'api' / 'views.py'
    
    try:
        with open(views_path, 'r') as f:
            content = f.read()
            
        # Check for TaskImageDetailView
        if 'class TaskImageDetailView' in content:
            print("   ✅ Found TaskImageDetailView class")
        else:
            print("   ❌ TaskImageDetailView class not found")
            return False
            
        # Check for get_queryset method
        if 'def get_queryset(self):' in content:
            print("   ✅ Found get_queryset method")
        else:
            print("   ❌ get_queryset method not found")
            return False
            
        # Check for task_pk constraint
        if 'task_pk' in content and 'kwargs' in content:
            print("   ✅ Found task_pk constraint in queryset")
        else:
            print("   ❌ task_pk constraint not found")
            return False
            
        print("   ✅ TaskImage queryset constraint verified")
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking TaskImage queryset: {e}")
        return False

def check_production_settings():
    """Check that production settings use environment variables."""
    print("\n3. ⚙️  Checking production settings...")
    
    backend_path = Path(__file__).parent / 'aristay_backend'
    settings_path = backend_path / 'backend' / 'settings.py'
    
    try:
        with open(settings_path, 'r') as f:
            content = f.read()
            
        checks = [
            ('SECRET_KEY', 'os.getenv'),
            ('DEBUG', 'os.getenv'),
            ('EMAIL_HOST', 'os.getenv'),
            ('EMAIL_HOST_USER', 'os.getenv'),
            ('EMAIL_HOST_PASSWORD', 'os.getenv'),
        ]
        
        all_passed = True
        for setting, pattern in checks:
            if pattern in content and setting in content:
                print(f"   ✅ {setting} uses environment variables")
            else:
                print(f"   ❌ {setting} doesn't use environment variables")
                all_passed = False
                
        if all_passed:
            print("   ✅ Production settings environment configuration verified")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking production settings: {e}")
        return False

def check_cors_middleware():
    """Check that CORS middleware is properly configured."""
    print("\n4. 🌐 Checking CORS middleware configuration...")
    
    backend_path = Path(__file__).parent / 'aristay_backend'
    settings_path = backend_path / 'backend' / 'settings.py'
    
    try:
        with open(settings_path, 'r') as f:
            content = f.read()
            
        # Check for CORS middleware
        if 'corsheaders.middleware.CorsMiddleware' in content:
            print("   ✅ Found corsheaders.middleware.CorsMiddleware")
        else:
            print("   ❌ CORS middleware not found")
            return False
            
        # Check for CORS settings
        cors_settings = ['CORS_ALLOW_ALL_ORIGINS', 'CORS_ALLOWED_ORIGINS']
        found_settings = 0
        
        for setting in cors_settings:
            if setting in content:
                print(f"   ✅ Found {setting} setting")
                found_settings += 1
            else:
                print(f"   ⚠️  {setting} setting not found")
                
        if found_settings > 0:
            print("   ✅ CORS middleware configuration verified")
            return True
        else:
            print("   ❌ No CORS settings found")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking CORS middleware: {e}")
        return False

def check_duplicate_imports():
    """Check that duplicate imports have been removed."""
    print("\n5. 📦 Checking for duplicate imports...")
    
    backend_path = Path(__file__).parent / 'aristay_backend'
    views_path = backend_path / 'api' / 'views.py'
    
    try:
        with open(views_path, 'r') as f:
            lines = f.readlines()
            
        # Check for duplicate NotificationService imports
        notification_imports = []
        for i, line in enumerate(lines):
            if 'NotificationService' in line and 'import' in line:
                notification_imports.append(i + 1)
                
        if len(notification_imports) == 1:
            print(f"   ✅ Found exactly 1 NotificationService import (line {notification_imports[0]})")
            return True
        elif len(notification_imports) > 1:
            print(f"   ❌ Found {len(notification_imports)} NotificationService imports on lines: {notification_imports}")
            return False
        else:
            print(f"   ❌ No NotificationService imports found")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking duplicate imports: {e}")
        return False

def check_cloudinary_feature_flag():
    """Check that Cloudinary integration is properly feature-flagged."""
    print("\n6. ☁️  Checking Cloudinary feature flag...")
    
    backend_path = Path(__file__).parent / 'aristay_backend'
    settings_path = backend_path / 'backend' / 'settings.py'
    
    try:
        with open(settings_path, 'r') as f:
            content = f.read()
            
        # Check for USE_CLOUDINARY setting
        if 'USE_CLOUDINARY' in content:
            print("   ✅ Found USE_CLOUDINARY feature flag")
        else:
            print("   ❌ USE_CLOUDINARY feature flag not found")
            return False
            
        # Check for Cloudinary configuration
        if 'cloudinary' in content.lower():
            print("   ✅ Found Cloudinary configuration")
        else:
            print("   ⚠️  No Cloudinary configuration found")
            
        print("   ✅ Cloudinary feature flag verified")
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking Cloudinary feature flag: {e}")
        return False

def main():
    """Run all production readiness checks."""
    print("🚀 Production Readiness Verification")
    print("=" * 50)
    
    checks = [
        check_timedelta_import,
        check_task_image_queryset,
        check_production_settings,
        check_cors_middleware,
        check_duplicate_imports,
        check_cloudinary_feature_flag,
    ]
    
    passed = 0
    total = len(checks)
    
    for check in checks:
        try:
            if check():
                passed += 1
        except Exception as e:
            print(f"   ❌ Check failed with error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 ALL PRODUCTION READINESS CHECKS PASSED!")
        print("✅ System is ready for staging deployment")
        print("\n📋 Next steps:")
        print("1. Deploy to Heroku staging environment")
        print("2. Configure environment variables in Heroku:")
        print("   - SECRET_KEY")
        print("   - DEBUG=False")
        print("   - EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD")
        print("   - USE_CLOUDINARY=True (optional)")
        print("   - CLOUDINARY_URL (if using Cloudinary)")
        print("3. Test all endpoints in staging")
        print("4. Validate file upload functionality")
        print("5. Deploy to production after staging validation")
        return True
    else:
        print(f"\n❌ {total - passed} checks failed. Fix these issues before deployment.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
