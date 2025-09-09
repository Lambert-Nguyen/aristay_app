#!/usr/bin/env python3
"""
Create sample checklist templates for common property management tasks
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import ChecklistTemplate, ChecklistItem

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample checklist templates for common tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing checklist templates before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing checklist templates...')
            ChecklistTemplate.objects.all().delete()
            self.stdout.write('✅ Cleared existing templates')

        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@aristay.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()

        # Create checklist templates
        self.create_cleaning_checklist(admin_user)
        self.create_maintenance_checklist(admin_user)
        self.create_inspection_checklist(admin_user)
        self.create_turnover_checklist(admin_user)

        self.stdout.write(
            self.style.SUCCESS('✅ Successfully created sample checklist templates!')
        )

    def create_cleaning_checklist(self, admin_user):
        """Create a comprehensive cleaning checklist"""
        template, created = ChecklistTemplate.objects.get_or_create(
            name='Standard Room Cleaning',
            defaults={
                'task_type': 'cleaning',
                'description': 'Complete room cleaning checklist for guest turnover',
                'is_active': True,
                'created_by': admin_user,
            }
        )

        if not created:
            self.stdout.write(f'Template "{template.name}" already exists, skipping...')
            return

        # Bathroom items
        bathroom_items = [
            ('Clean and disinfect toilet', 'blocking', True, 1),
            ('Clean and disinfect shower/bathtub', 'blocking', True, 2),
            ('Clean and disinfect sink and vanity', 'check', True, 3),
            ('Clean mirrors', 'check', True, 4),
            ('Restock toilet paper', 'check', True, 5),
            ('Restock hand towels', 'check', True, 6),
            ('Restock bath towels', 'check', True, 7),
            ('Empty trash and replace liner', 'check', True, 8),
            ('Sweep and mop floor', 'check', True, 9),
            ('Take before/after photos', 'photo_required', True, 10),
        ]

        # Bedroom items
        bedroom_items = [
            ('Strip all bedding', 'blocking', True, 1),
            ('Inspect mattress for stains/damage', 'check', True, 2),
            ('Vacuum mattress', 'check', True, 3),
            ('Make bed with fresh linens', 'blocking', True, 4),
            ('Dust all furniture', 'check', True, 5),
            ('Clean nightstands', 'check', True, 6),
            ('Clean dresser and closet', 'check', True, 7),
            ('Vacuum carpet/floor', 'check', True, 8),
            ('Empty trash', 'check', True, 9),
            ('Take before/after photos', 'photo_required', True, 10),
        ]

        # Kitchen items
        kitchen_items = [
            ('Clean and disinfect countertops', 'blocking', True, 1),
            ('Clean and disinfect sink', 'blocking', True, 2),
            ('Clean and disinfect stove/oven', 'check', True, 3),
            ('Clean and disinfect microwave', 'check', True, 4),
            ('Clean and disinfect refrigerator', 'check', True, 5),
            ('Clean and disinfect dishwasher', 'check', True, 6),
            ('Wash all dishes and put away', 'check', True, 7),
            ('Wipe down cabinets', 'check', True, 8),
            ('Sweep and mop floor', 'check', True, 9),
            ('Empty trash and replace liner', 'check', True, 10),
            ('Take before/after photos', 'photo_required', True, 11),
        ]

        # Living room items
        living_items = [
            ('Dust all furniture', 'check', True, 1),
            ('Vacuum upholstery', 'check', True, 2),
            ('Clean coffee table and end tables', 'check', True, 3),
            ('Vacuum carpet/floor', 'check', True, 4),
            ('Clean TV and electronics', 'check', True, 5),
            ('Empty trash', 'check', True, 6),
            ('Take before/after photos', 'photo_required', True, 7),
        ]

        # General items
        general_items = [
            ('Check all lights are working', 'check', True, 1),
            ('Check all windows and doors', 'check', True, 2),
            ('Check smoke detectors', 'check', True, 3),
            ('Check thermostat settings', 'check', True, 4),
            ('Final walkthrough inspection', 'check', True, 5),
            ('Take final completion photos', 'photo_required', True, 6),
        ]

        # Create all items
        all_items = [
            ('bathroom', bathroom_items),
            ('bedroom', bedroom_items),
            ('kitchen', kitchen_items),
            ('living_room', living_items),
            ('General', general_items),
        ]

        for room_type, items in all_items:
            for title, item_type, is_required, order in items:
                ChecklistItem.objects.create(
                    template=template,
                    title=title,
                    item_type=item_type,
                    is_required=is_required,
                    order=order,
                    room_type=room_type,
                )

        self.stdout.write(f'✅ Created "{template.name}" with {template.items.count()} items')

    def create_maintenance_checklist(self, admin_user):
        """Create a maintenance checklist"""
        template, created = ChecklistTemplate.objects.get_or_create(
            name='Property Maintenance',
            defaults={
                'task_type': 'maintenance',
                'description': 'Routine maintenance tasks for property upkeep',
                'is_active': True,
                'created_by': admin_user,
            }
        )

        if not created:
            self.stdout.write(f'Template "{template.name}" already exists, skipping...')
            return

        maintenance_items = [
            ('Check HVAC system operation', 'check', True, 1),
            ('Test all electrical outlets', 'check', True, 2),
            ('Check plumbing for leaks', 'check', True, 3),
            ('Inspect windows and doors', 'check', True, 4),
            ('Check smoke detectors and CO alarms', 'check', True, 5),
            ('Test garage door operation', 'check', True, 6),
            ('Inspect exterior for damage', 'check', True, 7),
            ('Check irrigation system', 'check', True, 8),
            ('Test pool equipment (if applicable)', 'check', False, 9),
            ('Document any issues found', 'text_input', True, 10),
            ('Take photos of any problems', 'photo_optional', False, 11),
        ]

        for title, item_type, is_required, order in maintenance_items:
            ChecklistItem.objects.create(
                template=template,
                title=title,
                item_type=item_type,
                is_required=is_required,
                order=order,
                room_type='General',
            )

        self.stdout.write(f'✅ Created "{template.name}" with {template.items.count()} items')

    def create_inspection_checklist(self, admin_user):
        """Create an inspection checklist"""
        template, created = ChecklistTemplate.objects.get_or_create(
            name='Property Inspection',
            defaults={
                'task_type': 'inspection',
                'description': 'Comprehensive property inspection checklist',
                'is_active': True,
                'created_by': admin_user,
            }
        )

        if not created:
            self.stdout.write(f'Template "{template.name}" already exists, skipping...')
            return

        inspection_items = [
            ('Exterior inspection - walls and roof', 'check', True, 1),
            ('Exterior inspection - windows and doors', 'check', True, 2),
            ('Exterior inspection - landscaping', 'check', True, 3),
            ('Interior inspection - living areas', 'check', True, 4),
            ('Interior inspection - bedrooms', 'check', True, 5),
            ('Interior inspection - bathrooms', 'check', True, 6),
            ('Interior inspection - kitchen', 'check', True, 7),
            ('Safety inspection - smoke detectors', 'check', True, 8),
            ('Safety inspection - electrical', 'check', True, 9),
            ('Safety inspection - plumbing', 'check', True, 10),
            ('Document findings', 'text_input', True, 11),
            ('Take inspection photos', 'photo_required', True, 12),
        ]

        for title, item_type, is_required, order in inspection_items:
            ChecklistItem.objects.create(
                template=template,
                title=title,
                item_type=item_type,
                is_required=is_required,
                order=order,
                room_type='General',
            )

        self.stdout.write(f'✅ Created "{template.name}" with {template.items.count()} items')

    def create_turnover_checklist(self, admin_user):
        """Create a guest turnover checklist"""
        template, created = ChecklistTemplate.objects.get_or_create(
            name='Guest Turnover',
            defaults={
                'task_type': 'cleaning',
                'description': 'Complete guest turnover process checklist',
                'is_active': True,
                'created_by': admin_user,
            }
        )

        if not created:
            self.stdout.write(f'Template "{template.name}" already exists, skipping...')
            return

        turnover_items = [
            ('Check for guest belongings', 'check', True, 1),
            ('Remove all trash', 'blocking', True, 2),
            ('Strip all bedding', 'blocking', True, 3),
            ('Clean all surfaces', 'blocking', True, 4),
            ('Restock amenities', 'check', True, 5),
            ('Test all appliances', 'check', True, 6),
            ('Check for damage', 'check', True, 7),
            ('Document any issues', 'text_input', True, 8),
            ('Take completion photos', 'photo_required', True, 9),
            ('Update property status', 'check', True, 10),
        ]

        for title, item_type, is_required, order in turnover_items:
            ChecklistItem.objects.create(
                template=template,
                title=title,
                item_type=item_type,
                is_required=is_required,
                order=order,
                room_type='General',
            )

        self.stdout.write(f'✅ Created "{template.name}" with {template.items.count()} items')
