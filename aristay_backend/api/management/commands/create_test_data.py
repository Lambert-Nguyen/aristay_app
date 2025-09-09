"""
Django management command to create comprehensive test data.

Usage: python manage.py create_test_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

from api.models import (
    Property, Booking, Task, Profile, PropertyOwnership, 
    Notification, ChecklistTemplate, ChecklistItem, TaskChecklist,
    CustomPermission, RolePermission, PropertyInventory, InventoryItem,
    InventoryCategory, AutoTaskTemplate, UserRole
)


class Command(BaseCommand):
    help = 'Create comprehensive test data for manual testing'

    def __init__(self):
        super().__init__()
        self.users = {}
        self.properties = []
        self.bookings = []
        self.tasks = []
        
    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write("🚀 Starting test data generation...")
        self.stdout.write("=" * 60)
        
        self.setup_permissions()
        self.create_users()
        self.create_properties()
        self.create_bookings()
        self.create_tasks()
        self.create_notifications()
        self.create_inventory_items()
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ TEST DATA GENERATION COMPLETE!"))
        self.stdout.write("=" * 60)
        
        self.stdout.write("\n📋 LOGIN CREDENTIALS:")
        self.stdout.write("Superuser: admin_super / admin123")
        self.stdout.write("Manager:   manager_alice / manager123")
        self.stdout.write("Staff:     staff_bob / staff123")
        self.stdout.write("Crew:      crew_charlie / crew123")
        self.stdout.write("           crew_diana / crew123")
        self.stdout.write("           crew_eve / crew123")
        
        self.stdout.write("\n🌐 ACCESS URLS:")
        self.stdout.write("Main Admin:    http://localhost:8000/admin/")
        self.stdout.write("Manager Site:  http://localhost:8000/manager/")
        self.stdout.write("Staff Portal:  http://localhost:8000/api/staff/")
        self.stdout.write("API Endpoints: http://localhost:8000/api/")
        
        self.stdout.write("\n📊 DATA SUMMARY:")
        self.stdout.write(f"Users: {User.objects.count()}")
        self.stdout.write(f"Properties: {Property.objects.count()}")
        self.stdout.write(f"Bookings: {Booking.objects.count()}")
        self.stdout.write(f"Tasks: {Task.objects.count()}")
        self.stdout.write(f"Notifications: {Notification.objects.count()}")
        
    def setup_permissions(self):
        """Ensure manager role has required permissions for testing"""
        self.stdout.write("Setting up permissions...")
        
        try:
            # Ensure manager_portal_access permission exists and is granted to manager role
            perm, created = CustomPermission.objects.get_or_create(
                name='manager_portal_access',
                defaults={'description': 'Access to the manager portal interface'}
            )
            
            role_perm, created = RolePermission.objects.get_or_create(
                role=UserRole.MANAGER,
                permission=perm,
                defaults={'granted': True, 'can_delegate': False}
            )
            
            if created:
                self.stdout.write(f"✅ Granted {perm.name} to manager role")
            elif not role_perm.granted:
                role_perm.granted = True
                role_perm.save()
                self.stdout.write(f"✅ Updated {perm.name} for manager role")
            else:
                self.stdout.write(f"✅ Permission {perm.name} already granted to manager role")
                
        except Exception as e:
            self.stdout.write(f"❌ Error setting up permissions: {e}")
        
    def create_users(self):
        """Create test users for each role"""
        self.stdout.write("Creating test users...")
        
        # 1. SUPERUSER - Full system access
        superuser, created = User.objects.get_or_create(
            username='admin_super',
            defaults={
                'email': 'superuser@aristay.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                # Don't set is_staff/is_superuser - let Profile.role sync handle it
            }
        )
        if created:
            superuser.set_password('admin123')
            superuser.save()
            
        # Create superuser profile - this will trigger the sync
        profile, created = Profile.objects.get_or_create(
            user=superuser,
            defaults={
                'role': UserRole.SUPERUSER,  # This will auto-sync is_staff=True, is_superuser=True
                'phone_number': '+1-555-0001',
                'address': '123 Admin Street, City, ST 12345'
            }
        )
        # Update role if profile already existed but with wrong role
        if not created and profile.role != UserRole.SUPERUSER:
            profile.role = UserRole.SUPERUSER
            profile.save()
        
        # Manually trigger sync for superusers
        if profile.role == UserRole.SUPERUSER:
            superuser.is_staff = True
            superuser.is_superuser = True
            superuser.save(update_fields=['is_staff', 'is_superuser'])
        
        self.users['superuser'] = superuser
        self.stdout.write(f"✅ Superuser created: {superuser.username} (role: {profile.role})")
        
        # 2. MANAGER - Property oversight and staff management
        manager, created = User.objects.get_or_create(
            username='manager_alice',
            defaults={
                'email': 'alice.manager@aristay.com',
                'first_name': 'Alice',
                'last_name': 'Manager',
                # Don't set is_staff/is_superuser - let Profile.role sync handle it
            }
        )
        if created:
            manager.set_password('manager123')
            manager.save()
            
        profile, created = Profile.objects.get_or_create(
            user=manager,
            defaults={
                'role': UserRole.MANAGER,  # This will auto-sync is_staff=True, is_superuser=False
                'phone_number': '+1-555-0002',
                'address': '456 Manager Ave, City, ST 12345'
            }
        )
        # Update role if profile already existed but with wrong role
        if not created and profile.role != UserRole.MANAGER:
            profile.role = UserRole.MANAGER
            profile.save()
        
        # Manually trigger sync for managers
        if profile.role == UserRole.MANAGER:
            manager.is_staff = True
            manager.is_superuser = False
            manager.save(update_fields=['is_staff', 'is_superuser'])
        
        self.users['manager'] = manager
        self.stdout.write(f"✅ Manager created: {manager.username} (role: {profile.role})")
        
        # 3. STAFF/CREW - Task execution
        staff, created = User.objects.get_or_create(
            username='staff_bob',
            defaults={
                'email': 'bob.staff@aristay.com',
                'first_name': 'Bob',
                'last_name': 'Cleaner',
                # Don't set is_staff/is_superuser - let Profile.role sync handle it
            }
        )
        if created:
            staff.set_password('staff123')
            staff.save()
            
        profile, created = Profile.objects.get_or_create(
            user=staff,
            defaults={
                'role': UserRole.STAFF,  # This will auto-sync is_staff=False, is_superuser=False
                'phone_number': '+1-555-0003',
                'address': '789 Staff Road, City, ST 12345'
            }
        )
        # Update role if profile already existed but with wrong role
        if not created and profile.role != UserRole.STAFF:
            profile.role = UserRole.STAFF
            profile.save()
        
        # Manually trigger sync for staff
        if profile.role == UserRole.STAFF:
            staff.is_staff = False
            staff.is_superuser = False
            staff.save(update_fields=['is_staff', 'is_superuser'])
        
        self.users['staff'] = staff
        self.stdout.write(f"✅ Staff created: {staff.username} (role: {profile.role})")
        
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
                    # Don't set is_staff/is_superuser - let Profile.role sync handle it
                }
            )
            if created:
                user.set_password('crew123')
                user.save()
                
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'role': UserRole.STAFF,  # This will auto-sync is_staff=False, is_superuser=False
                    'phone_number': f'+1-555-000{i+2}',
                    'address': f'{(i+2)*100} Crew Lane, City, ST 12345'
                }
            )
            # Update role if profile already existed but with wrong role
            if not created and profile.role != UserRole.STAFF:
                profile.role = UserRole.STAFF
                profile.save()
            
            # Manually trigger sync for crew
            if profile.role == UserRole.STAFF:
                user.is_staff = False
                user.is_superuser = False
                user.save(update_fields=['is_staff', 'is_superuser'])
            
            self.users[username] = user
            self.stdout.write(f"✅ Crew member created: {user.username} (role: {profile.role})")
    
    def create_properties(self):
        """Create test properties"""
        self.stdout.write("\nCreating test properties...")
        
        property_data = [
            {
                'name': 'Sunset Villa',
                'address': '123 Beach Front Dr, Santa Monica, CA 90401',
            },
            {
                'name': 'Downtown Loft',
                'address': '456 Urban St, Los Angeles, CA 90015',
            },
            {
                'name': 'Mountain Cabin',
                'address': '789 Pine Tree Rd, Big Bear, CA 92315',
            },
            {
                'name': 'City Condo',
                'address': '321 High Rise Ave, San Francisco, CA 94105',
            }
        ]
        
        for prop_data in property_data:
            prop, created = Property.objects.get_or_create(
                name=prop_data['name'],
                defaults=prop_data
            )
            self.properties.append(prop)
            self.stdout.write(f"✅ Property created: {prop.name}")
            
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
        self.stdout.write("\nCreating test bookings...")
        
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
            self.stdout.write(f"✅ Booking created: {booking.guest_name} at {booking.property.name}")
    
    def create_tasks(self):
        """Create test tasks"""
        self.stdout.write("\nCreating test tasks...")
        
        now = timezone.now()
        
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
            self.stdout.write(f"✅ Task created: {task.title}")
    
    def create_notifications(self):
        """Create test notifications"""
        self.stdout.write("\nCreating test notifications...")
        
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
            self.stdout.write(f"✅ Notification created: {notif.verb} → {notif.task.title}")
    
    def create_inventory_items(self):
        """Create sample inventory"""
        self.stdout.write("\nCreating inventory items...")
        
        # First, create categories
        categories = [
            {'name': 'Cleaning', 'description': 'Cleaning supplies and chemicals', 'icon': '🧽'},
            {'name': 'Linens', 'description': 'Towels, sheets, and bedding', 'icon': '🛏️'},
            {'name': 'Maintenance', 'description': 'Maintenance tools and supplies', 'icon': '🔧'},
            {'name': 'Amenities', 'description': 'Guest amenities and supplies', 'icon': '🎁'},
        ]
        
        category_objects = {}
        for cat_data in categories:
            cat, created = InventoryCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            category_objects[cat_data['name']] = cat
            if created:
                self.stdout.write(f"✅ Category created: {cat.name}")
        
        # Sample inventory items with correct categories
        inventory_data = [
            # Cleaning supplies
            {'name': 'All-Purpose Cleaner', 'category': category_objects['Cleaning'], 'unit': 'bottle'},
            {'name': 'Toilet Paper', 'category': category_objects['Cleaning'], 'unit': 'roll'},
            {'name': 'Towels', 'category': category_objects['Linens'], 'unit': 'each'},
            {'name': 'Bed Sheets', 'category': category_objects['Linens'], 'unit': 'each'},
            # Maintenance supplies  
            {'name': 'Light Bulbs', 'category': category_objects['Maintenance'], 'unit': 'each'},
            {'name': 'Pool Chemicals', 'category': category_objects['Maintenance'], 'unit': 'bottle'},
            # Amenities
            {'name': 'Welcome Basket', 'category': category_objects['Amenities'], 'unit': 'each'},
            {'name': 'Coffee Pods', 'category': category_objects['Amenities'], 'unit': 'box'},
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
                        'par_level': random.randint(2, 10),
                        'max_level': random.randint(20, 100),
                        'storage_location': f'{prop.name} Storage Room'
                    }
                )
            
            self.stdout.write(f"✅ Inventory item created: {item.name}")
