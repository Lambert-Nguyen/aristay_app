"""
Management command to set up department groups and migrate existing user roles
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User
from api.models import DepartmentGroups, UserRole, Profile


class Command(BaseCommand):
    help = 'Set up department groups and migrate existing user roles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # 1. Create department groups
        self.stdout.write('Creating department groups...')
        departments_created = 0
        
        for dept_name in DepartmentGroups.get_all_departments():
            if not dry_run:
                group, created = Group.objects.get_or_create(name=dept_name)
                if created:
                    departments_created += 1
                    self.stdout.write(f'  ✅ Created group: {dept_name}')
                else:
                    self.stdout.write(f'  ℹ️  Group exists: {dept_name}')
            else:
                exists = Group.objects.filter(name=dept_name).exists()
                if not exists:
                    departments_created += 1
                    self.stdout.write(f'  🔮 Would create group: {dept_name}')
                else:
                    self.stdout.write(f'  ℹ️  Group exists: {dept_name}')
        
        # 2. Migrate existing user roles
        self.stdout.write('\nMigrating existing user roles...')
        
        # Map old role values to new structure
        role_migrations = {
            'cleaning': {'new_role': UserRole.STAFF, 'department': DepartmentGroups.CLEANING},
            'maintenance': {'new_role': UserRole.STAFF, 'department': DepartmentGroups.MAINTENANCE},
            'laundry': {'new_role': UserRole.STAFF, 'department': DepartmentGroups.LAUNDRY},
            'lawn_pool': {'new_role': UserRole.STAFF, 'department': DepartmentGroups.LAWN_POOL},
            'owner': {'new_role': UserRole.SUPERUSER, 'department': None},
            # staff, manager, viewer remain the same
        }
        
        users_updated = 0
        departments_assigned = 0
        
        for profile in Profile.objects.all():
            user = profile.user
            old_role = profile.role
            changes = []
            
            # Check if this is an old role that needs migration
            if old_role in role_migrations:
                migration = role_migrations[old_role]
                new_role = migration['new_role']
                department = migration['department']
                
                # Update role
                if not dry_run:
                    profile.role = new_role
                    profile.save()
                changes.append(f'role: {old_role} → {new_role}')
                
                # Add to department if specified
                if department:
                    if not dry_run:
                        profile.add_to_department(department)
                    changes.append(f'added to department: {department}')
                    departments_assigned += 1
                
                users_updated += 1
                action_prefix = '🔮 Would update' if dry_run else '✅ Updated'
                self.stdout.write(f'  {action_prefix} {user.username}: {", ".join(changes)}')
            
            # Handle superuser flag sync
            elif user.is_superuser and profile.role != UserRole.SUPERUSER:
                if not dry_run:
                    profile.role = UserRole.SUPERUSER
                    profile.save()
                changes.append(f'synced superuser: {old_role} → {UserRole.SUPERUSER}')
                users_updated += 1
                action_prefix = '🔮 Would sync' if dry_run else '✅ Synced'
                self.stdout.write(f'  {action_prefix} {user.username}: {", ".join(changes)}')
        
        # 3. Summary
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN COMPLETE - No changes made'))
        else:
            self.stdout.write(self.style.SUCCESS('MIGRATION COMPLETE'))
        
        self.stdout.write(f'Department groups: {departments_created} created')
        self.stdout.write(f'User roles: {users_updated} updated')
        self.stdout.write(f'Department assignments: {departments_assigned} made')
        
        # 4. Show current state
        self.stdout.write('\nCurrent user roles and departments:')
        for profile in Profile.objects.select_related('user').all():
            user = profile.user
            departments = profile.get_departments()
            dept_str = f" ({', '.join(departments)})" if departments else ""
            self.stdout.write(f'  {user.username}: {profile.get_role_display()}{dept_str}')
            
        if dry_run:
            self.stdout.write(self.style.WARNING('\nRun without --dry-run to apply changes'))
