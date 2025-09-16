#!/usr/bin/env python3
"""
Optimized sample checklist templates creation with memory management
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction, connection
from api.models import ChecklistTemplate, ChecklistItem
import gc

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample checklist templates for common tasks (memory optimized)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing checklist templates before creating new ones',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Batch size for bulk operations (default: 50)',
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        
        try:
            with transaction.atomic():
                if options['clear']:
                    self.stdout.write('Clearing existing checklist templates...')
                    # Use bulk operations for better performance
                    ChecklistTemplate.objects.all().delete()
                    self.stdout.write('✅ Cleared existing templates')

                # Get or create admin user
                admin_user, created = User.objects.get_or_create(
                    username='admin',
                    defaults={
                        'email': 'admin@aristay.com',
                        'is_superuser': True,
                    }
                )
                if created:
                    admin_user.set_password('admin123')
                    admin_user.save()

                # Create checklist templates with memory management
                self.create_cleaning_checklist(admin_user, batch_size)
                self.create_maintenance_checklist(admin_user, batch_size)
                self.create_inspection_checklist(admin_user, batch_size)
                self.create_turnover_checklist(admin_user, batch_size)

                # Force garbage collection
                gc.collect()
                
                # Close database connections
                connection.close()

                self.stdout.write(
                    self.style.SUCCESS('✅ Successfully created sample checklist templates!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating checklists: {str(e)}')
            )
            raise
        finally:
            # Ensure connections are closed
            connection.close()
            gc.collect()

    def create_cleaning_checklist(self, admin_user, batch_size=50):
        """Create comprehensive room cleaning checklist with memory optimization"""
        template, created = ChecklistTemplate.objects.get_or_create(
            name='Standard Room Cleaning',
            defaults={
                'description': 'Comprehensive cleaning checklist for all room types',
                'created_by': admin_user,
            }
        )
        
        if not created:
            return

        # Define cleaning items in batches
        cleaning_items = [
            # Bathroom Items
            {'text': 'Clean and disinfect toilet bowl', 'category': 'bathroom', 'order': 1},
            {'text': 'Wipe down toilet seat and lid', 'category': 'bathroom', 'order': 2},
            {'text': 'Clean and disinfect sink and faucet', 'category': 'bathroom', 'order': 3},
            {'text': 'Wipe down mirror and vanity', 'category': 'bathroom', 'order': 4},
            {'text': 'Clean shower/tub and fixtures', 'category': 'bathroom', 'order': 5},
            {'text': 'Wipe down shower doors/curtain', 'category': 'bathroom', 'order': 6},
            {'text': 'Clean bathroom floor and baseboards', 'category': 'bathroom', 'order': 7},
            {'text': 'Restock toilet paper', 'category': 'bathroom', 'order': 8},
            {'text': 'Restock hand towels', 'category': 'bathroom', 'order': 9},
            {'text': 'Restock bath towels', 'category': 'bathroom', 'order': 10},
            {'text': 'Restock soap and shampoo', 'category': 'bathroom', 'order': 11},
            {'text': 'Empty bathroom trash', 'category': 'bathroom', 'order': 12},
            
            # Bedroom Items
            {'text': 'Strip and remake bed with fresh linens', 'category': 'bedroom', 'order': 13},
            {'text': 'Vacuum mattress and flip if needed', 'category': 'bedroom', 'order': 14},
            {'text': 'Dust all furniture surfaces', 'category': 'bedroom', 'order': 15},
            {'text': 'Clean nightstands and dressers', 'category': 'bedroom', 'order': 16},
            {'text': 'Vacuum carpet/clean hard floors', 'category': 'bedroom', 'order': 17},
            {'text': 'Dust window sills and blinds', 'category': 'bedroom', 'order': 18},
            {'text': 'Clean closet and organize items', 'category': 'bedroom', 'order': 19},
            {'text': 'Check and clean light fixtures', 'category': 'bedroom', 'order': 20},
            {'text': 'Empty bedroom trash', 'category': 'bedroom', 'order': 21},
            
            # Kitchen Items
            {'text': 'Clean and disinfect countertops', 'category': 'kitchen', 'order': 22},
            {'text': 'Clean sink and faucet', 'category': 'kitchen', 'order': 23},
            {'text': 'Clean inside and outside of microwave', 'category': 'kitchen', 'order': 24},
            {'text': 'Clean inside and outside of refrigerator', 'category': 'kitchen', 'order': 25},
            {'text': 'Clean stovetop and oven', 'category': 'kitchen', 'order': 26},
            {'text': 'Clean dishwasher inside and out', 'category': 'kitchen', 'order': 27},
            {'text': 'Wipe down cabinet fronts', 'category': 'kitchen', 'order': 28},
            {'text': 'Clean kitchen floor', 'category': 'kitchen', 'order': 29},
            {'text': 'Empty kitchen trash', 'category': 'kitchen', 'order': 30},
            {'text': 'Restock paper towels', 'category': 'kitchen', 'order': 31},
            {'text': 'Restock dish soap', 'category': 'kitchen', 'order': 32},
            
            # Living Area Items
            {'text': 'Dust all furniture and surfaces', 'category': 'living', 'order': 33},
            {'text': 'Vacuum carpets/clean hard floors', 'category': 'living', 'order': 34},
            {'text': 'Clean coffee table and end tables', 'category': 'living', 'order': 35},
            {'text': 'Dust and clean TV and entertainment center', 'category': 'living', 'order': 36},
            {'text': 'Clean windows and window sills', 'category': 'living', 'order': 37},
            {'text': 'Vacuum/clean couches and chairs', 'category': 'living', 'order': 38},
            {'text': 'Dust light fixtures and ceiling fans', 'category': 'living', 'order': 39},
            {'text': 'Clean baseboards and trim', 'category': 'living', 'order': 40},
            {'text': 'Empty living area trash', 'category': 'living', 'order': 41},
            {'text': 'Check and replace light bulbs', 'category': 'living', 'order': 42},
            {'text': 'Test smoke detectors', 'category': 'living', 'order': 43},
            {'text': 'Check thermostat and temperature', 'category': 'living', 'order': 44},
        ]

        # Create items in batches to manage memory
        for i in range(0, len(cleaning_items), batch_size):
            batch = cleaning_items[i:i + batch_size]
            items_to_create = []
            
            for item_data in batch:
                items_to_create.append(ChecklistItem(
                    template=template,
                    text=item_data['text'],
                    category=item_data['category'],
                    order=item_data['order']
                ))
            
            # Bulk create items
            ChecklistItem.objects.bulk_create(items_to_create)
            
            # Clear the batch from memory
            del items_to_create
            gc.collect()

        self.stdout.write(f'✅ Created "Standard Room Cleaning" with {len(cleaning_items)} items')

    def create_maintenance_checklist(self, admin_user, batch_size=50):
        """Create property maintenance checklist"""
        template, created = ChecklistTemplate.objects.get_or_create(
            name='Property Maintenance',
            defaults={
                'description': 'Regular maintenance tasks for property upkeep',
                'created_by': admin_user,
            }
        )
        
        if not created:
            return

        maintenance_items = [
            {'text': 'Check HVAC system operation', 'category': 'hvac', 'order': 1},
            {'text': 'Replace HVAC filters', 'category': 'hvac', 'order': 2},
            {'text': 'Test smoke and carbon monoxide detectors', 'category': 'safety', 'order': 3},
            {'text': 'Check and clean gutters', 'category': 'exterior', 'order': 4},
            {'text': 'Inspect exterior for damage', 'category': 'exterior', 'order': 5},
            {'text': 'Test all electrical outlets', 'category': 'electrical', 'order': 6},
            {'text': 'Check plumbing for leaks', 'category': 'plumbing', 'order': 7},
            {'text': 'Test all door locks and handles', 'category': 'security', 'order': 8},
            {'text': 'Check window operation and seals', 'category': 'windows', 'order': 9},
            {'text': 'Inspect and clean outdoor areas', 'category': 'exterior', 'order': 10},
            {'text': 'Check water pressure and temperature', 'category': 'plumbing', 'order': 11},
        ]

        # Create items in batches
        for i in range(0, len(maintenance_items), batch_size):
            batch = maintenance_items[i:i + batch_size]
            items_to_create = []
            
            for item_data in batch:
                items_to_create.append(ChecklistItem(
                    template=template,
                    text=item_data['text'],
                    category=item_data['category'],
                    order=item_data['order']
                ))
            
            ChecklistItem.objects.bulk_create(items_to_create)
            del items_to_create
            gc.collect()

        self.stdout.write(f'✅ Created "Property Maintenance" with {len(maintenance_items)} items')

    def create_inspection_checklist(self, admin_user, batch_size=50):
        """Create property inspection checklist"""
        template, created = ChecklistTemplate.objects.get_or_create(
            name='Property Inspection',
            defaults={
                'description': 'Comprehensive property inspection checklist',
                'created_by': admin_user,
            }
        )
        
        if not created:
            return

        inspection_items = [
            {'text': 'Check all lights and switches', 'category': 'electrical', 'order': 1},
            {'text': 'Test all appliances', 'category': 'appliances', 'order': 2},
            {'text': 'Inspect walls for damage', 'category': 'interior', 'order': 3},
            {'text': 'Check floors for wear or damage', 'category': 'interior', 'order': 4},
            {'text': 'Test all doors and windows', 'category': 'security', 'order': 5},
            {'text': 'Check bathroom fixtures', 'category': 'bathroom', 'order': 6},
            {'text': 'Inspect kitchen appliances', 'category': 'kitchen', 'order': 7},
            {'text': 'Check heating and cooling', 'category': 'hvac', 'order': 8},
            {'text': 'Test smoke detectors', 'category': 'safety', 'order': 9},
            {'text': 'Check exterior condition', 'category': 'exterior', 'order': 10},
            {'text': 'Inspect outdoor areas', 'category': 'exterior', 'order': 11},
            {'text': 'Document any issues found', 'category': 'documentation', 'order': 12},
        ]

        # Create items in batches
        for i in range(0, len(inspection_items), batch_size):
            batch = inspection_items[i:i + batch_size]
            items_to_create = []
            
            for item_data in batch:
                items_to_create.append(ChecklistItem(
                    template=template,
                    text=item_data['text'],
                    category=item_data['category'],
                    order=item_data['order']
                ))
            
            ChecklistItem.objects.bulk_create(items_to_create)
            del items_to_create
            gc.collect()

        self.stdout.write(f'✅ Created "Property Inspection" with {len(inspection_items)} items')

    def create_turnover_checklist(self, admin_user, batch_size=50):
        """Create guest turnover checklist"""
        template, created = ChecklistTemplate.objects.get_or_create(
            name='Guest Turnover',
            defaults={
                'description': 'Complete guest turnover process checklist',
                'created_by': admin_user,
            }
        )
        
        if not created:
            return

        turnover_items = [
            {'text': 'Remove all personal items', 'category': 'preparation', 'order': 1},
            {'text': 'Strip all bedding and linens', 'category': 'bedroom', 'order': 2},
            {'text': 'Empty all trash containers', 'category': 'cleaning', 'order': 3},
            {'text': 'Clean and sanitize bathroom', 'category': 'bathroom', 'order': 4},
            {'text': 'Clean and sanitize kitchen', 'category': 'kitchen', 'order': 5},
            {'text': 'Vacuum and clean all floors', 'category': 'cleaning', 'order': 6},
            {'text': 'Dust all surfaces', 'category': 'cleaning', 'order': 7},
            {'text': 'Check and restock supplies', 'category': 'supplies', 'order': 8},
            {'text': 'Test all appliances', 'category': 'appliances', 'order': 9},
            {'text': 'Final walkthrough inspection', 'category': 'inspection', 'order': 10},
        ]

        # Create items in batches
        for i in range(0, len(turnover_items), batch_size):
            batch = turnover_items[i:i + batch_size]
            items_to_create = []
            
            for item_data in batch:
                items_to_create.append(ChecklistItem(
                    template=template,
                    text=item_data['text'],
                    category=item_data['category'],
                    order=item_data['order']
                ))
            
            ChecklistItem.objects.bulk_create(items_to_create)
            del items_to_create
            gc.collect()

        self.stdout.write(f'✅ Created "Guest Turnover" with {len(turnover_items)} items')
