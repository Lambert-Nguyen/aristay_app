#!/usr/bin/env python
"""
Simple script to test calendar URL generation fix
"""
import os
import sys
import django

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings_test')
django.setup()

from django.urls import reverse

def test_url_generation():
    """Test that URLs are generated correctly"""
    print("Testing calendar URL generation fix...")
    
    # Test task URL generation
    task_id = 123
    task_url = reverse('portal-task-detail', args=[task_id])
    print(f"Task URL: {task_url}")
    assert task_url.startswith('/api/portal/tasks/')
    assert str(task_id) in task_url
    print("✓ Task URL generation works correctly")
    
    # Test booking URL generation
    property_id = 456
    booking_id = 789
    booking_url = reverse('portal-booking-detail', args=[property_id, booking_id])
    print(f"Booking URL: {booking_url}")
    assert booking_url.startswith('/api/portal/properties/')
    assert str(property_id) in booking_url
    assert str(booking_id) in booking_url
    print("✓ Booking URL generation works correctly")
    
    print("\n🎉 All URL generation tests passed!")
    print("The calendar URL fix is working correctly.")

if __name__ == '__main__':
    test_url_generation()
