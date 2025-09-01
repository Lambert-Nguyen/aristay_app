"""
Management command to set up default permissions for the dynamic permission system
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import (
    CustomPermission, RolePermission, UserRole, Profile
)


class Command(BaseCommand):
    help = 'Set up default permissions for the dynamic permission system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all permissions (delete existing)',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Resetting all permissions...')
            RolePermission.objects.all().delete()
            CustomPermission.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('All permissions have been reset.')
            )

        # Create all custom permissions
        self.create_permissions()
        
        # Set up role permissions
        self.setup_role_permissions()
        
        # Create default superuser if none exists
        self.create_default_superuser()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Permission system setup completed successfully!')
        )

    def create_permissions(self):
        """Create all custom permissions"""
        self.stdout.write('Creating custom permissions...')
        
        permissions = [
            # Property Management
            ('view_properties', 'View Properties'),
            ('add_properties', 'Add Properties'),
            ('change_properties', 'Edit Properties'),
            ('delete_properties', 'Delete Properties'),
            
            # Booking Management
            ('view_bookings', 'View Bookings'),
            ('add_bookings', 'Add Bookings'),
            ('change_bookings', 'Edit Bookings'),
            ('delete_bookings', 'Delete Bookings'),
            ('import_bookings', 'Import Bookings from Excel'),
            
            # Task Management
            ('view_tasks', 'View Tasks'),
            ('add_tasks', 'Add Tasks'),
            ('change_tasks', 'Edit Tasks'),
            ('delete_tasks', 'Delete Tasks'),
            ('assign_tasks', 'Assign Tasks to Others'),
            ('view_all_tasks', 'View All Tasks (not just own)'),
            
            # User Management
            ('view_users', 'View Users'),
            ('add_users', 'Add Users'),
            ('change_users', 'Edit Users'),
            ('delete_users', 'Delete Users'),
            ('manage_user_permissions', 'Manage User Permissions'),
            
            # Reports and Analytics
            ('view_reports', 'View Reports'),
            ('export_data', 'Export Data'),
            ('view_analytics', 'View Analytics Dashboard'),
            
            # System Administration
            ('access_admin_panel', 'Access Admin Panel'),
            ('manager_portal_access', 'Manager Portal Access'),
            ('manage_system_settings', 'Manage System Settings'),
            ('view_system_logs', 'View System Logs'),
            ('manage_notifications', 'Manage Notifications'),
            
            # Checklist Management
            ('view_checklists', 'View Checklists'),
            ('add_checklists', 'Add Checklists'),
            ('change_checklists', 'Edit Checklists'),
            ('delete_checklists', 'Delete Checklists'),
            
            # Device Management
            ('view_devices', 'View Devices'),
            ('add_devices', 'Add Devices'),
            ('change_devices', 'Edit Devices'),
            ('delete_devices', 'Delete Devices'),
            
            # File Management
            ('excel_import_access', 'Excel Import Access'),
            ('file_upload_access', 'File Upload Access'),
        ]
        
        created_count = 0
        for perm_name, perm_description in permissions:
            perm, created = CustomPermission.objects.get_or_create(
                name=perm_name,
                defaults={
                    'description': perm_description,
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created permission: {perm_name}')
            else:
                self.stdout.write(f'  - Permission already exists: {perm_name}')
        
        self.stdout.write(f'Created {created_count} new permissions.')

    def setup_role_permissions(self):
        """Set up default permissions for each role"""
        self.stdout.write('Setting up role permissions...')
        
        # Superuser gets all permissions
        self.setup_superuser_permissions()
        
        # Manager gets most permissions
        self.setup_manager_permissions()
        
        # Staff gets limited permissions
        self.setup_staff_permissions()
        
        # Viewer gets minimal permissions
        self.setup_viewer_permissions()

    def setup_superuser_permissions(self):
        """Set up superuser permissions"""
        self.stdout.write('  Setting up SUPERUSER permissions...')
        
        superuser_permissions = [
            'view_properties', 'add_properties', 'change_properties', 'delete_properties',
            'view_bookings', 'add_bookings', 'change_bookings', 'delete_bookings', 'import_bookings',
            'view_tasks', 'add_tasks', 'change_tasks', 'delete_tasks', 'assign_tasks', 'view_all_tasks',
            'view_users', 'add_users', 'change_users', 'delete_users', 'manage_user_permissions',
            'view_reports', 'export_data', 'view_analytics',
            'access_admin_panel', 'manager_portal_access', 'manage_system_settings', 'view_system_logs', 'manage_notifications',
            'view_checklists', 'add_checklists', 'change_checklists', 'delete_checklists',
            'view_devices', 'add_devices', 'change_devices', 'delete_devices',
            'excel_import_access', 'file_upload_access'
        ]
        
        for perm_name in superuser_permissions:
            try:
                perm = CustomPermission.objects.get(name=perm_name)
                role_perm, created = RolePermission.objects.get_or_create(
                    role=UserRole.SUPERUSER,
                    permission=perm,
                    defaults={
                        'granted': True,
                        'can_delegate': True
                    }
                )
                if created:
                    self.stdout.write(f'    ✓ {perm_name}')
            except CustomPermission.DoesNotExist:
                self.stdout.write(f'    ✗ Permission not found: {perm_name}')

    def setup_manager_permissions(self):
        """Set up manager permissions"""
        self.stdout.write('  Setting up MANAGER permissions...')
        
        manager_permissions = [
            # Can view and manage most things
            ('view_properties', True, True),
            ('add_properties', True, False),
            ('change_properties', True, False),
            ('delete_properties', False, False),
            
            ('view_bookings', True, True),
            ('add_bookings', True, False),
            ('change_bookings', True, False),
            ('delete_bookings', False, False),
            ('import_bookings', True, False),
            
            ('view_tasks', True, True),
            ('add_tasks', True, False),
            ('change_tasks', True, False),
            ('delete_tasks', False, False),
            ('assign_tasks', True, False),
            ('view_all_tasks', True, False),
            
            ('view_users', True, False),
            ('add_users', True, False),
            ('change_users', True, False),
            ('delete_users', False, False),
            ('manage_user_permissions', False, False),
            
            ('view_reports', True, False),
            ('export_data', True, False),
            ('view_analytics', True, False),
            
            ('manager_portal_access', True, False),
            ('manage_notifications', True, False),
            
            ('view_checklists', True, False),
            ('add_checklists', True, False),
            ('change_checklists', True, False),
            ('delete_checklists', False, False),
            
            ('view_devices', True, False),
            ('add_devices', True, False),
            ('change_devices', True, False),
            ('delete_devices', False, False),
            
            ('excel_import_access', True, False),
            ('file_upload_access', True, False),
        ]
        
        for perm_name, granted, can_delegate in manager_permissions:
            try:
                perm = CustomPermission.objects.get(name=perm_name)
                role_perm, created = RolePermission.objects.get_or_create(
                    role=UserRole.MANAGER,
                    permission=perm,
                    defaults={
                        'granted': granted,
                        'can_delegate': can_delegate
                    }
                )
                if created:
                    self.stdout.write(f'    ✓ {perm_name} (granted: {granted}, delegate: {can_delegate})')
            except CustomPermission.DoesNotExist:
                self.stdout.write(f'    ✗ Permission not found: {perm_name}')

    def setup_staff_permissions(self):
        """Set up staff permissions"""
        self.stdout.write('  Setting up STAFF permissions...')
        
        staff_permissions = [
            # Limited permissions for staff
            ('view_properties', True, False),
            ('view_bookings', True, False),
            ('view_tasks', True, False),
            ('add_tasks', True, False),
            ('change_tasks', False, False),  # Can only edit their own tasks
            ('delete_tasks', False, False),
            ('view_checklists', True, False),
            ('view_devices', True, False),
        ]
        
        for perm_name, granted, can_delegate in staff_permissions:
            try:
                perm = CustomPermission.objects.get(name=perm_name)
                role_perm, created = RolePermission.objects.get_or_create(
                    role=UserRole.STAFF,
                    permission=perm,
                    defaults={
                        'granted': granted,
                        'can_delegate': can_delegate
                    }
                )
                if created:
                    self.stdout.write(f'    ✓ {perm_name} (granted: {granted})')
            except CustomPermission.DoesNotExist:
                self.stdout.write(f'    ✗ Permission not found: {perm_name}')

    def setup_viewer_permissions(self):
        """Set up viewer permissions"""
        self.stdout.write('  Setting up VIEWER permissions...')
        
        viewer_permissions = [
            # Read-only permissions
            ('view_properties', True, False),
            ('view_bookings', True, False),
            ('view_tasks', True, False),
            ('view_checklists', True, False),
            ('view_devices', True, False),
        ]
        
        for perm_name, granted, can_delegate in viewer_permissions:
            try:
                perm = CustomPermission.objects.get(name=perm_name)
                role_perm, created = RolePermission.objects.get_or_create(
                    role=UserRole.VIEWER,
                    permission=perm,
                    defaults={
                        'granted': granted,
                        'can_delegate': can_delegate
                    }
                )
                if created:
                    self.stdout.write(f'    ✓ {perm_name} (read-only)')
            except CustomPermission.DoesNotExist:
                self.stdout.write(f'    ✗ Permission not found: {perm_name}')

    def create_default_superuser(self):
        """Create a default superuser if none exists"""
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Creating default superuser...')
            
            # Check if teststaff user exists
            if User.objects.filter(username='teststaff').exists():
                user = User.objects.get(username='teststaff')
                user.is_superuser = True
                user.is_staff = True
                user.save()
                
                # Update profile role
                profile, created = Profile.objects.get_or_create(
                    user=user,
                    defaults={'role': UserRole.SUPERUSER}
                )
                if not created:
                    profile.role = UserRole.SUPERUSER
                    profile.save()
                
                self.stdout.write('  ✓ Updated teststaff user to superuser')
            else:
                # Create new superuser
                user = User.objects.create_user(
                    username='admin',
                    email='admin@aristay.com',
                    password='admin123',
                    is_superuser=True,
                    is_staff=True
                )
                Profile.objects.create(user=user, role=UserRole.SUPERUSER)
                self.stdout.write('  ✓ Created default superuser: admin/admin123')
        else:
            self.stdout.write('  - Superuser already exists')
