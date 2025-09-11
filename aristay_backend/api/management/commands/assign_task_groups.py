#!/usr/bin/env python3
"""
Management command to assign task groups to existing users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import Profile, TaskGroup, UserRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Assign task groups to existing users based on their roles or manually'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auto-assign',
            action='store_true',
            help='Automatically assign task groups based on user roles and groups',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Assign task group to specific user',
        )
        parser.add_argument(
            '--task-group',
            type=str,
            choices=[choice[0] for choice in TaskGroup.choices],
            help='Task group to assign',
        )
        parser.add_argument(
            '--list-groups',
            action='store_true',
            help='List all available task groups',
        )
        parser.add_argument(
            '--show-users',
            action='store_true',
            help='Show all users and their current task groups',
        )

    def handle(self, *args, **options):
        if options['list_groups']:
            self.list_task_groups()
            return

        if options['show_users']:
            self.show_users()
            return

        if options['auto_assign']:
            self.auto_assign_task_groups()
            return

        if options['username'] and options['task_group']:
            self.assign_specific_user(options['username'], options['task_group'])
            return

        self.stdout.write(
            self.style.WARNING(
                'Please specify an action. Use --help for available options.'
            )
        )

    def list_task_groups(self):
        """List all available task groups"""
        self.stdout.write(self.style.SUCCESS('Available Task Groups:'))
        self.stdout.write('=' * 40)
        for choice in TaskGroup.choices:
            self.stdout.write(f'  {choice[0]:<15} - {choice[1]}')

    def show_users(self):
        """Show all users and their current task groups"""
        self.stdout.write(self.style.SUCCESS('Users and Task Groups:'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'{"Username":<20} {"Role":<12} {"Task Group":<15} {"Status"}')
        self.stdout.write('-' * 60)

        for user in User.objects.all().select_related('profile'):
            try:
                profile = user.profile
                role = profile.get_role_display()
                task_group = profile.get_task_group_display()
                status = "✅" if profile.task_group != TaskGroup.NONE else "❌"
            except Profile.DoesNotExist:
                role = "No Profile"
                task_group = "Not Assigned"
                status = "❌"

            self.stdout.write(
                f'{user.username:<20} {role:<12} {task_group:<15} {status}'
            )

    def auto_assign_task_groups(self):
        """Automatically assign task groups based on user roles and groups"""
        self.stdout.write(self.style.SUCCESS('Auto-assigning task groups...'))
        
        # Mapping of Django groups to task groups
        group_mapping = {
            'Cleaning': TaskGroup.CLEANING,
            'Maintenance': TaskGroup.MAINTENANCE,
            'Laundry': TaskGroup.LAUNDRY,
            'Lawn Pool': TaskGroup.LAWN_POOL,
        }

        assigned_count = 0
        for user in User.objects.all():
            try:
                profile = user.profile
            except Profile.DoesNotExist:
                # Create profile if it doesn't exist
                profile = Profile.objects.create(user=user)
                self.stdout.write(f'Created profile for {user.username}')

            # Skip if already assigned
            if profile.task_group != TaskGroup.NONE:
                continue

            # Check user's groups for task group assignment
            user_groups = [group.name for group in user.groups.all()]
            assigned = False

            for group_name, task_group in group_mapping.items():
                if group_name in user_groups:
                    profile.task_group = task_group
                    profile.save()
                    self.stdout.write(
                        f'✅ Assigned {user.username} to {task_group} (based on {group_name} group)'
                    )
                    assigned_count += 1
                    assigned = True
                    break

            # If no group-based assignment, assign based on role
            if not assigned and profile.role == UserRole.STAFF:
                profile.task_group = TaskGroup.GENERAL
                profile.save()
                self.stdout.write(
                    f'✅ Assigned {user.username} to {TaskGroup.GENERAL} (default for staff)'
                )
                assigned_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'✅ Auto-assigned task groups to {assigned_count} users')
        )

    def assign_specific_user(self, username, task_group):
        """Assign task group to a specific user"""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" not found')
            )
            return

        try:
            profile = user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=user)
            self.stdout.write(f'Created profile for {user.username}')

        old_task_group = profile.get_task_group_display()
        profile.task_group = task_group
        profile.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Updated {user.username}: {old_task_group} → {profile.get_task_group_display()}'
            )
        )
