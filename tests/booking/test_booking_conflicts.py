#!/usr/bin/env python
"""
Test script to demonstrate the new conflict detection functionality
"""
import os
import sys
import django
from datetime import datetime, date, timedelta

# Add the project directory to the Python path
sys.path.append('/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Booking, Property
from django.utils import timezone

def test_conflict_detection():
    """Test the conflict detection functionality"""
    print("Testing Booking Conflict Detection...")
    print("=" * 50)
    
    # Get all bookings to test
    bookings = Booking.objects.all()[:5]  # Test first 5 bookings
    
    if not bookings:
        print("No bookings found in database.")
        return
    
    for booking in bookings:
        print(f"\nBooking ID: {booking.id}")
        print(f"Property: {booking.property.name}")
        print(f"Guest: {booking.guest_name}")
        print(f"Dates: {booking.check_in_date.date()} to {booking.check_out_date.date()}")
        print(f"Source: {booking.source or 'N/A'}")
        print(f"External Code: {booking.external_code or 'N/A'}")
        print(f"Booked On: {booking.booked_on.date() if booking.booked_on else 'N/A'}")
        
        # Test conflict detection
        conflicts = booking.check_conflicts()
        flag = booking.get_conflict_flag()
        details = booking.get_conflict_details()
        
        print(f"Conflict Flag: {flag}")
        if conflicts:
            print("Conflict Details:")
            for conflict in conflicts:
                print(f"  - {conflict['type']}: {conflict['message']} (Severity: {conflict['severity']})")
        else:
            print("No conflicts detected")
        
        print("-" * 40)

if __name__ == "__main__":
    test_conflict_detection()
