#!/usr/bin/env python3
"""
Debug the exact location of the ZIP file error
"""

import os
import django
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
import pandas as pd
import io
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_excel_import():
    """Debug the Excel import step by step"""
    
    User = get_user_model()
    user = User.objects.get(id=1)
    
    excel_file_path = "/Users/duylam1407/Workspace/SJSU/aristay_app/docs/requirements/Cleaning_schedule_1.xlsx"
    
    print("=== Step-by-step debugging ===")
    
    # Step 1: Create Django uploaded file
    with open(excel_file_path, 'rb') as f:
        file_content = f.read()
    
    uploaded_file = SimpleUploadedFile(
        name="debug.xlsx",
        content=file_content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    print(f"1. File created: {uploaded_file.size} bytes")
    
    # Step 2: Test direct Excel reading
    print("2. Testing direct Excel reading...")
    try:
        df = pd.read_excel(io.BytesIO(file_content), sheet_name='Cleaning schedule', engine='openpyxl')
        print(f"   ✅ Success! {len(df)} rows")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    # Step 3: Test after file operations
    print("3. Testing file seek operations...")
    uploaded_file.seek(0)
    content_copy = uploaded_file.read()
    print(f"   File read: {len(content_copy)} bytes")
    
    try:
        df = pd.read_excel(io.BytesIO(content_copy), sheet_name='Cleaning schedule', engine='openpyxl')
        print(f"   ✅ BytesIO with copy: {len(df)} rows")
    except Exception as e:
        print(f"   ❌ BytesIO with copy failed: {e}")
    
    # Step 4: Import log creation simulation
    print("4. Testing import log creation...")
    from api.models import BookingImportLog, BookingImportTemplate, Property
    
    # Reset file
    uploaded_file.seek(0)
    
    try:
        # Simulate creating import log
        template, created = BookingImportTemplate.objects.get_or_create(
            name="Debug Template",
            defaults={
                'import_type': 'csv',
                'auto_create_tasks': True,
                'created_by': user
            }
        )
        
        import_log = BookingImportLog.objects.create(
            template=template,
            import_file=uploaded_file,
            total_rows=0,
            successful_imports=0,
            errors_count=0,
            errors_log='debug test',
            imported_by=user
        )
        print("   ✅ Import log created successfully")
        
        # Now try reading the file after the log creation
        print("5. Testing Excel reading after import log creation...")
        uploaded_file.seek(0)
        current_content = uploaded_file.read()
        print(f"   File readable after log: {len(current_content)} bytes")
        
        if len(current_content) > 0:
            try:
                df = pd.read_excel(io.BytesIO(current_content), sheet_name='Cleaning schedule', engine='openpyxl')
                print(f"   ✅ Excel read after log: {len(df)} rows")
            except Exception as e:
                print(f"   ❌ Excel read after log failed: {e}")
        else:
            print("   ❌ File is empty after import log creation!")
        
        # Clean up
        import_log.delete()
        
    except Exception as e:
        print(f"   ❌ Import log creation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_excel_import()
