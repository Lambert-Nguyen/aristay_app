#!/usr/bin/env python
import os
import sys
import django

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings_local')
django.setup()

from api.models import TaskImage

print("=== TaskImage Database Check ===")
print(f"Total TaskImage records: {TaskImage.objects.count()}")

if TaskImage.objects.count() > 0:
    print("\nSample records:")
    for img in TaskImage.objects.all()[:10]:
        print(f"  ID: {img.id}, Task: {img.task_id}, Type: {img.photo_type}, Seq: {img.sequence_number}")
    
    print("\nDuplicate constraint violations:")
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT task_id, photo_type, sequence_number, COUNT(*) as count
            FROM api_taskimage 
            GROUP BY task_id, photo_type, sequence_number 
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            for dup in duplicates:
                print(f"  Task {dup[0]}, Type {dup[1]}, Seq {dup[2]}: {dup[3]} records")
        else:
            print("  No duplicates found")
else:
    print("No TaskImage records found")

print("\n=== Cleaning up test data ===")
# Delete all TaskImage records to clean up test data
deleted_count = TaskImage.objects.all().delete()[0]
print(f"Deleted {deleted_count} TaskImage records")

print("Database cleanup complete!")
