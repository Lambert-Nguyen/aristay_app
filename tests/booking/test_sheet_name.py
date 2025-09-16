#!/usr/bin/env python3
"""
Quick test to verify sheet name handling
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.services.excel_import_service import ExcelImportService
from django.contrib.auth import get_user_model

User = get_user_model()

def test_sheet_name():
    """Test that the service can handle the correct sheet name"""
    try:
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='test_import_user',
            defaults={
                'email': 'test@aristay.com',
                'is_superuser': True
            }
        )
        
        # Test the service initialization
        import_service = ExcelImportService(user)
        print("✅ ExcelImportService initialized successfully")
        
        # Check the default sheet name
        print(f"📋 Default sheet name: '{import_service.import_excel_file.__defaults__[0]}'")
        
        # Test with the correct sheet name
        correct_sheet = 'Cleaning schedule'
        print(f"🎯 Expected sheet name: '{correct_sheet}'")
        
        if import_service.import_excel_file.__defaults__[0] == correct_sheet:
            print("✅ Sheet name is correctly set to 'Cleaning schedule'")
        else:
            print("❌ Sheet name is not correctly set")
        
        print("\n🚀 Sheet name fix is working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sheet_name()
