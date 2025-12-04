#!/usr/bin/env python3
"""
Create comprehensive test data for manual testing of all user workflows.

This script creates:
1. Superuser - Full system admin access
2. Manager - Property management and staff oversight
3. Staff/Crew - Task execution and property maintenance

Usage: python create_test_data.py
"""

import os
import sys
import django
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

# Add Django project to path and setup
sys.path.append('aristay_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
os.chdir('aristay_backend')
django.setup()

from api.models import (
    Property, Booking, Task, Profile, PropertyOwnership, 
    Notification, ChecklistTemplate, ChecklistItem, TaskChecklist,
    CustomPermission, RolePermission, PropertyInventory, InventoryItem,
    LostFound, AutoTaskTemplate
)

class TestDataGenerator:
    def __init__(self):
        self.users = {}
        self.properties = []
        self.bookings = []
        self.tasks = []
        
    def create_users(self):
        """Create test users for each role"""
        print("Creating test users...")
        
        # 1. SUPERUSER - Full system access
        superuser, created = User.objects.get_or_create(
            username='admin_super',
            defaults={
                'email': 'superuser@aristay.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            superuser.set_password('admin123')
            superuser.save()
            
        # Create superuser profile
        Profile.objects.get_or_create(
            user=superuser,
            defaults={
                'role': 'admin',
                'phone_number': '+1-555-0001',
                'address': '123 Admin Street, City, ST 12345'
            }
        )
        
        self.users['superuser'] = superuser
        print(f"✅ Superuser created: {superuser.username}")
        
        # 2. MANAGER - Property oversight and staff management
        manager, created = User.objects.get_or_create(
            username='manager_alice',
            defaults={
                'email': 'alice.manager@aristay.com',
                'first_name': 'Alice',
                'last_name': 'Manager',
                'is_staff': True,
                'is_superuser': False,
            }
        )
        if created:
            manager.set_password('manager123')
            manager.save()
            
        Profile.objects.get_or_create(
            user=manager,
            defaults={
                'role': 'manager',
                'phone_number': '+1-555-0002',
                'address': '456 Manager Ave, City, ST 12345'
            }
        )
        
        self.users['manager'] = manager
        print(f"✅ Manager created: {manager.username}")
        
        # 3. STAFF/CREW - Task execution
        staff, created = User.objects.get_or_create(
            username='staff_bob',
            defaults={
                'email': 'bob.staff@aristay.com',
                'first_name': 'Bob',
                'last_name': 'Cleaner',
                'is_staff': False,
                'is_superuser': False,
            }
        )
        if created:
            staff.set_password('staff123')
            staff.save()
            
        Profile.objects.get_or_create(
            user=staff,
            defaults={
                'role': 'staff',
                'phone_number': '+1-555-0003',
                'address': '789 Staff Road, City, ST 12345'
            }
        )
        
        self.users['staff'] = staff
        print(f"✅ Staff created: {staff.username}")
        
        # Additional Staff Members
        for i, (username, name) in enumerate([
            ('crew_charlie', 'Charlie Maintenance'),
            ('crew_diana', 'Diana Laundry'),
            ('crew_eve', 'Eve Pool')
        ], 2):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@aristay.com',
                    'first_name': name.split()[0],
                    'last_name': name.split()[1],
                    'is_staff': False,
                    'is_superuser': False,
                }
            )
            if created:
                user.set_password('crew123')
                user.save()
                
            Profile.objects.get_or_create(
                user=user,
                defaults={
                    'role': 'staff',
                    'phone_number': f'+1-555-000{i+2}',
                    'address': f'{(i+2)*100} Crew Lane, City, ST 12345'
                }
            )
            
            self.users[username] = user
            print(f"✅ Crew member created: {user.username}")
    
    def create_properties(self):
        """Create test properties"""
        print("\nCreating test properties...")
        
        property_data = [
            {
                'name': 'Sunset Villa',
                'address': '123 Beach Front Dr, Santa Monica, CA 90401',
                'description': 'Luxury beachfront villa with ocean views',
                'property_type': 'villa'
            },
            {
                'name': 'Downtown Loft',
                'address': '456 Urban St, Los Angeles, CA 90015',
                'description': 'Modern loft in downtown LA',
                'property_type': 'apartment'
            },
            {
                'name': 'Mountain Cabin',
                'address': '789 Pine Tree Rd, Big Bear, CA 92315',
                'description': 'Cozy mountain cabin with fireplace',
                'property_type': 'cabin'
            },
            {
                'name': 'City Condo',
                'address': '321 High Rise Ave, San Francisco, CA 94105',
                'description': 'High-rise condo with city views',
                'property_type': 'condo'
            }
        ]
        
        for prop_data in property_data:
            prop, created = Property.objects.get_or_create(
                name=prop_data['name'],
                defaults=prop_data
            )
            self.properties.append(prop)
            print(f"✅ Property created: {prop.name}")
            
            # Assign property ownership
            # Manager owns all properties
            PropertyOwnership.objects.get_or_create(
                property=prop,
                user=self.users['manager'],
                defaults={
                    'ownership_type': 'manager',
                    'can_edit': True
                }
            )
    
    def create_bookings(self):
        """Create test bookings"""
        print("\nCreating test bookings...")
        
        now = timezone.now()
        
        booking_data = [
            {
                'property': self.properties[0],  # Sunset Villa
                'guest_name': 'John & Sarah Smith',
                'guest_contact': 'john.smith@email.com',
                'check_in_date': now + timedelta(days=2),
                'check_out_date': now + timedelta(days=5),
                'status': 'confirmed',
                'external_code': 'AIR123456',
                'source': 'Airbnb',
                'adults': 2,
                'children': 0
            },
            {
                'property': self.properties[1],  # Downtown Loft
                'guest_name': 'Maria Garcia',
                'guest_contact': 'maria.garcia@email.com',
                'check_in_date': now + timedelta(days=1),
                'check_out_date': now + timedelta(days=3),
                'status': 'booked',
                'external_code': 'VRB789012',
                'source': 'VRBO',
                'adults': 1,
                'children': 1
            },
            {
                'property': self.properties[2],  # Mountain Cabin
                'guest_name': 'The Johnson Family',
                'guest_contact': 'johnson.family@email.com',
                'check_in_date': now + timedelta(days=7),
                'check_out_date': now + timedelta(days=10),
                'status': 'confirmed',
                'external_code': 'DIR345678',
                'source': 'Direct',
                'adults': 4,
                'children': 2
            },
            {
                'property': self.properties[0],  # Sunset Villa (past booking)
                'guest_name': 'David Wilson',
                'guest_contact': 'david.wilson@email.com',
                'check_in_date': now - timedelta(days=3),
                'check_out_date': now - timedelta(days=1),
                'status': 'completed',
                'external_code': 'AIR654321',
                'source': 'Airbnb',
                'adults': 1,
                'children': 0
            }
        ]
        
        for booking_info in booking_data:
            booking, created = Booking.objects.get_or_create(
                external_code=booking_info['external_code'],
                defaults=booking_info
            )
            self.bookings.append(booking)
            print(f"✅ Booking created: {booking.guest_name} at {booking.property.name}")
    
    def create_tasks(self):
        """Create test tasks"""
        print("\nCreating test tasks...")
        
        now = timezone.now()
        staff_users = [self.users['staff'], self.users['crew_charlie'], 
                      self.users['crew_diana'], self.users['crew_eve']]
        
        task_data = [
            {
                'title': 'Pre-arrival Cleaning - Sunset Villa',
                'description': 'Deep clean and prepare for John & Sarah Smith arrival',
                'task_type': 'cleaning',
                'property_ref': self.properties[0],
                'booking': self.bookings[0],
                'status': 'pending',
                'assigned_to': self.users['staff'],
                'due_date': self.bookings[0].check_in_date - timedelta(hours=2),
                'created_by': self.users['manager']
            },
            {
                'title': 'Post-checkout Cleaning - Sunset Villa',
                'description': 'Clean after David Wilson checkout',
                'task_type': 'cleaning',
                'property_ref': self.properties[0],
                'booking': self.bookings[3],
                'status': 'in-progress',
                'assigned_to': self.users['staff'],
                'due_date': self.bookings[3].check_out_date + timedelta(hours=1),
                'created_by': self.users['manager']
            },
            {
                'title': 'Downtown Loft - Pre-arrival Setup',
                'description': 'Setup and welcome amenities for Maria Garcia',
                'task_type': 'cleaning',
                'property_ref': self.properties[1],
                'booking': self.bookings[1],
                'status': 'pending',
                'assigned_to': self.users['crew_diana'],
                'due_date': self.bookings[1].check_in_date - timedelta(hours=1),
                'created_by': self.users['manager']
            },
            {
                'title': 'Mountain Cabin - HVAC Maintenance',
                'description': 'Check heating system before Johnson family arrival',
                'task_type': 'maintenance',
                'property_ref': self.properties[2],
                'booking': self.bookings[2],
                'status': 'pending',
                'assigned_to': self.users['crew_charlie'],
                'due_date': self.bookings[2].check_in_date - timedelta(days=1),
                'created_by': self.users['manager']
            },
            {
                'title': 'City Condo - Routine Inspection',
                'description': 'Weekly routine inspection and maintenance check',
                'task_type': 'maintenance',
                'property_ref': self.properties[3],
                'status': 'completed',
                'assigned_to': self.users['crew_charlie'],
                'due_date': now - timedelta(days=2),
                'created_by': self.users['manager']
            },
            {
                'title': 'Pool Maintenance - Sunset Villa',
                'description': 'Weekly pool cleaning and chemical balance',
                'task_type': 'maintenance',
                'property_ref': self.properties[0],
                'status': 'pending',
                'assigned_to': self.users['crew_eve'],
                'due_date': now + timedelta(days=1),
                'created_by': self.users['manager']
            }
        ]
        
        for task_info in task_data:
            task, created = Task.objects.get_or_create(
                title=task_info['title'],
                defaults=task_info
            )
            self.tasks.append(task)
            print(f"✅ Task created: {task.title}")
    
    def create_notifications(self):
        """Create test notifications"""
        print("\nCreating test notifications...")
        
        # Notifications for different users
        notification_data = [
            {
                'recipient': self.users['staff'],
                'task': self.tasks[0],  # Pre-arrival cleaning
                'verb': 'assigned',
                'read': False
            },
            {
                'recipient': self.users['crew_charlie'],
                'task': self.tasks[3],  # HVAC maintenance
                'verb': 'assigned',
                'read': False
            },
            {
                'recipient': self.users['manager'],
                'task': self.tasks[4],  # Completed inspection
                'verb': 'status_changed',
                'read': True
            },
            {
                'recipient': self.users['staff'],
                'task': self.tasks[1],  # Post-checkout cleaning
                'verb': 'status_changed',
                'read': False
            }
        ]
        
        for notif_data in notification_data:
            notif, created = Notification.objects.get_or_create(
                recipient=notif_data['recipient'],
                task=notif_data['task'],
                verb=notif_data['verb'],
                defaults={'read': notif_data['read']}
            )
            print(f"✅ Notification created: {notif.verb} → {notif.task.title}")
    
    def create_inventory_items(self):
        """Create sample inventory"""
        print("\nCreating inventory items...")
        
        # Sample inventory categories and items
        inventory_data = [
            # Cleaning supplies
            {'name': 'All-Purpose Cleaner', 'category': 'Cleaning', 'unit': 'bottles'},
            {'name': 'Toilet Paper', 'category': 'Cleaning', 'unit': 'rolls'},
            {'name': 'Towels', 'category': 'Linens', 'unit': 'pieces'},
            {'name': 'Bed Sheets', 'category': 'Linens', 'unit': 'sets'},
            # Maintenance supplies  
            {'name': 'Light Bulbs', 'category': 'Maintenance', 'unit': 'pieces'},
            {'name': 'Pool Chemicals', 'category': 'Maintenance', 'unit': 'containers'},
            # Amenities
            {'name': 'Welcome Basket', 'category': 'Amenities', 'unit': 'pieces'},
            {'name': 'Coffee Pods', 'category': 'Amenities', 'unit': 'boxes'},
        ]
        
        for item_data in inventory_data:
            item, created = InventoryItem.objects.get_or_create(
                name=item_data['name'],
                defaults=item_data
            )
            
            # Add inventory to each property
            for prop in self.properties:
                PropertyInventory.objects.get_or_create(
                    property_ref=prop,
                    item=item,
                    defaults={
                        'current_stock': random.randint(5, 50),
                        'minimum_threshold': random.randint(2, 10),
                        'maximum_capacity': random.randint(20, 100),
                        'storage_location': f'{prop.name} Storage Room'
                    }
                )
            
            print(f"✅ Inventory item created: {item.name}")
    
    def run(self):
        """Run the complete test data generation"""
        print("🚀 Starting test data generation...")
        print("=" * 60)
        
        self.create_users()
        self.create_properties()
        self.create_bookings()
        self.create_tasks()
        self.create_notifications()
        self.create_inventory_items()
        
        print("\n" + "=" * 60)
        print("✅ TEST DATA GENERATION COMPLETE!")
        print("=" * 60)
        
        print("\n📋 LOGIN CREDENTIALS:")
        print("Superuser: admin_super / admin123")
        print("Manager:   manager_alice / manager123")
        print("Staff:     staff_bob / staff123")
        print("Crew:      crew_charlie / crew123")
        print("           crew_diana / crew123")
        print("           crew_eve / crew123")
        
        print("\n🌐 ACCESS URLS:")
        print("Main Admin:    http://localhost:8000/admin/")
        print("Manager Site:  http://localhost:8000/manager/")
        print("Staff Portal:  http://localhost:8000/api/staff/")
        print("API Endpoints: http://localhost:8000/api/")
        
        print("\n📊 DATA SUMMARY:")
        print(f"Users: {User.objects.count()}")
        print(f"Properties: {Property.objects.count()}")
        print(f"Bookings: {Booking.objects.count()}")
        print(f"Tasks: {Task.objects.count()}")
        print(f"Notifications: {Notification.objects.count()}")

if __name__ == '__main__':
    generator = TestDataGenerator()
    generator.run()
