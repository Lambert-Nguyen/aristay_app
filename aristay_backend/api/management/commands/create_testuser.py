from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Profile

class Command(BaseCommand):
    help = 'Create or update test user for authentication testing'

    def add_arguments(self, parser):
        parser.add_argument('--password', type=str, default='testpass123', help='Password for test user')

    def handle(self, *args, **options):
        password = options['password']
        
        # Create or get testuser
        testuser, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True,
            }
        )
        
        # Set password
        testuser.set_password(password)
        testuser.save()
        
        # Create or get profile
        profile, profile_created = Profile.objects.get_or_create(
            user=testuser,
            defaults={
                'role': 'staff',
                'timezone': 'America/New_York'
            }
        )
        
        status = "Created" if created else "Updated"
        profile_status = "Created" if profile_created else "Found"
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{status} testuser: {testuser.username}\n'
                f'{profile_status} profile with role: {profile.get_role_display()}\n'
                f'Password: {password}\n'
                f'Active: {testuser.is_active}\n'
                f'Staff: {testuser.is_staff}\n'
                f'Superuser: {testuser.is_superuser}'
            )
        )
