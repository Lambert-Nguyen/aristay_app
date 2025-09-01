# api/management/commands/setup_default_permissions.py

from django.core.management.base import BaseCommand
from api.models import CustomPermission, RolePermission, UserRole


class Command(BaseCommand):
    help = 'Set up default permissions for all roles'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default permissions...')
        
        # Create all permissions first
        permissions_created = 0
        for permission_name, description in CustomPermission.PERMISSION_CHOICES:
            permission, created = CustomPermission.objects.get_or_create(
                name=permission_name,
                defaults={'description': description}
            )
            if created:
                permissions_created += 1
                self.stdout.write(f'Created permission: {permission_name}')
        
        self.stdout.write(f'Total permissions created: {permissions_created}')
        
        # Define default permissions for each role
        role_permissions = {
            UserRole.SUPERUSER: {
                # Superuser gets all permissions with delegation rights
                'permissions': [perm[0] for perm in CustomPermission.PERMISSION_CHOICES],
                'delegatable': [perm[0] for perm in CustomPermission.PERMISSION_CHOICES]
            },
            UserRole.MANAGER: {
                'permissions': [
                    # Property Management
                    'view_properties', 'add_properties', 'change_properties',
                    
                    # Booking Management
                    'view_bookings', 'add_bookings', 'change_bookings', 'import_bookings',
                    
                    # Task Management
                    'view_tasks', 'add_tasks', 'change_tasks', 'assign_tasks', 'view_all_tasks',
                    
                    # User Management (limited)
                    'view_users', 'change_users',
                    
                    # Reports and Analytics
                    'view_reports', 'export_data', 'view_analytics',
                    
                    # Checklist Management
                    'view_checklists', 'add_checklists', 'change_checklists',
                    
                    # Device Management
                    'view_devices', 'add_devices', 'change_devices',
                    
                    # Notifications
                    'manage_notifications',
                ],
                'delegatable': [
                    # Managers can delegate these to staff
                    'view_properties', 'view_bookings', 'view_tasks', 'change_tasks',
                    'view_checklists', 'change_checklists', 'view_devices',
                ]
            },
            UserRole.STAFF: {
                'permissions': [
                    # Basic viewing
                    'view_properties', 'view_bookings', 'view_tasks',
                    
                    # Task management for assigned tasks
                    'change_tasks',
                    
                    # Checklist viewing
                    'view_checklists',
                    
                    # Device viewing
                    'view_devices',
                ],
                'delegatable': []  # Staff cannot delegate permissions
            },
            UserRole.VIEWER: {
                'permissions': [
                    # Read-only access
                    'view_properties', 'view_bookings', 'view_tasks',
                    'view_checklists', 'view_devices', 'view_reports',
                ],
                'delegatable': []  # Viewers cannot delegate permissions
            }
        }
        
        # Set up role permissions
        role_perms_created = 0
        for role, config in role_permissions.items():
            for permission_name in config['permissions']:
                try:
                    permission = CustomPermission.objects.get(name=permission_name)
                    can_delegate = permission_name in config.get('delegatable', [])
                    
                    role_perm, created = RolePermission.objects.get_or_create(
                        role=role,
                        permission=permission,
                        defaults={
                            'granted': True,
                            'can_delegate': can_delegate
                        }
                    )
                    
                    if created:
                        role_perms_created += 1
                        delegate_text = " (can delegate)" if can_delegate else ""
                        self.stdout.write(f'Created role permission: {role} -> {permission_name}{delegate_text}')
                    
                except CustomPermission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Permission {permission_name} not found')
                    )
        
        self.stdout.write(f'Total role permissions created: {role_perms_created}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up default permissions!')
        )
        
        # Display summary
        self.stdout.write('\n=== PERMISSION SUMMARY ===')
        for role in [UserRole.SUPERUSER, UserRole.MANAGER, UserRole.STAFF, UserRole.VIEWER]:
            role_display = dict(UserRole.choices)[role]
            perms = RolePermission.objects.filter(role=role, granted=True)
            delegatable_perms = perms.filter(can_delegate=True)
            
            self.stdout.write(f'\n{role_display}:')
            self.stdout.write(f'  Total permissions: {perms.count()}')
            self.stdout.write(f'  Can delegate: {delegatable_perms.count()}')
            
            if delegatable_perms.exists():
                self.stdout.write('  Delegatable permissions:')
                for perm in delegatable_perms:
                    self.stdout.write(f'    - {perm.permission.get_name_display()}')
