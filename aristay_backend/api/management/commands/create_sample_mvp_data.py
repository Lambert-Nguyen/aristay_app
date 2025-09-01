"""
Management command to create sample data for MVP Phase 1 testing.
Creates checklist templates, inventory items, and sample workflow data.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import (
    Property, ChecklistTemplate, ChecklistItem, InventoryCategory, InventoryItem,
    PropertyInventory, Task, TaskChecklist, ChecklistResponse
)


class Command(BaseCommand):
    help = 'Create sample MVP Phase 1 data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample MVP Phase 1 data...')
        
        # Get or create a superuser for creating data
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
            self.stdout.write(f'Created admin user: admin/admin123')

        # Create sample properties if none exist
        if not Property.objects.exists():
            properties = [
                {'name': 'Ocean View Villa', 'address': '123 Beach Blvd, Miami, FL'},
                {'name': 'Downtown Loft', 'address': '456 City Center, Tampa, FL'},
                {'name': 'Mountain Cabin', 'address': '789 Pine Ridge, Gatlinburg, TN'},
            ]
            for prop_data in properties:
                Property.objects.create(created_by=admin_user, **prop_data)
            self.stdout.write(f'Created {len(properties)} sample properties')

        # Create Checklist Templates
        self.create_checklist_templates(admin_user)
        
        # Create Inventory System
        self.create_inventory_system(admin_user)
        
        self.stdout.write(self.style.SUCCESS('Sample MVP data created successfully!'))

    def create_checklist_templates(self, admin_user):
        """Create task-specific checklist templates."""
        
        # Cleaning Checklist Template
        cleaning_template, created = ChecklistTemplate.objects.get_or_create(
            name='Standard Room Cleaning',
            task_type='cleaning',
            defaults={
                'description': 'Comprehensive room cleaning checklist for all room types',
                'created_by': admin_user,
            }
        )
        
        if created:
            cleaning_items = [
                # Bathroom items
                {'title': 'Clean and disinfect toilet', 'room_type': 'bathroom', 'item_type': 'blocking', 'order': 1},
                {'title': 'Clean shower/bathtub', 'room_type': 'bathroom', 'item_type': 'blocking', 'order': 2},
                {'title': 'Clean sink and mirror', 'room_type': 'bathroom', 'item_type': 'check', 'order': 3},
                {'title': 'Photo of clean bathroom', 'room_type': 'bathroom', 'item_type': 'photo_required', 'order': 4},
                {'title': 'Restock towels and amenities', 'room_type': 'bathroom', 'item_type': 'check', 'order': 5},
                
                # Bedroom items
                {'title': 'Strip and remake bed with fresh linens', 'room_type': 'bedroom', 'item_type': 'blocking', 'order': 1},
                {'title': 'Vacuum carpet/mop floors', 'room_type': 'bedroom', 'item_type': 'blocking', 'order': 2},
                {'title': 'Dust all surfaces', 'room_type': 'bedroom', 'item_type': 'check', 'order': 3},
                {'title': 'Photo of clean bedroom', 'room_type': 'bedroom', 'item_type': 'photo_required', 'order': 4},
                {'title': 'Check all lighting and electronics', 'room_type': 'bedroom', 'item_type': 'check', 'order': 5},
                
                # Kitchen items  
                {'title': 'Clean all appliances inside and out', 'room_type': 'kitchen', 'item_type': 'blocking', 'order': 1},
                {'title': 'Clean countertops and sink', 'room_type': 'kitchen', 'item_type': 'check', 'order': 2},
                {'title': 'Mop floor', 'room_type': 'kitchen', 'item_type': 'check', 'order': 3},
                {'title': 'Photo of clean kitchen', 'room_type': 'kitchen', 'item_type': 'photo_required', 'order': 4},
                {'title': 'Restock basic supplies', 'room_type': 'kitchen', 'item_type': 'check', 'order': 5},
                
                # Living room items
                {'title': 'Vacuum furniture and floors', 'room_type': 'living_room', 'item_type': 'check', 'order': 1},
                {'title': 'Dust all surfaces and decor', 'room_type': 'living_room', 'item_type': 'check', 'order': 2},
                {'title': 'Photo of clean living area', 'room_type': 'living_room', 'item_type': 'photo_required', 'order': 3},
                
                # Overall completion
                {'title': 'Final walkthrough completed', 'room_type': '', 'item_type': 'blocking', 'order': 99},
                {'title': 'Note any damages or issues', 'room_type': '', 'item_type': 'text_input', 'order': 100},
            ]
            
            for item_data in cleaning_items:
                ChecklistItem.objects.create(
                    template=cleaning_template,
                    **item_data
                )
            
            self.stdout.write(f'Created cleaning checklist template with {len(cleaning_items)} items')

        # Maintenance Checklist Template
        maintenance_template, created = ChecklistTemplate.objects.get_or_create(
            name='Property Maintenance Inspection',
            task_type='maintenance',
            defaults={
                'description': 'Regular maintenance and inspection checklist',
                'created_by': admin_user,
            }
        )
        
        if created:
            maintenance_items = [
                {'title': 'Check HVAC system operation', 'item_type': 'blocking', 'order': 1},
                {'title': 'Inspect plumbing fixtures', 'item_type': 'blocking', 'order': 2},
                {'title': 'Test all electrical outlets and switches', 'item_type': 'check', 'order': 3},
                {'title': 'Photo of any maintenance issues', 'item_type': 'photo_optional', 'order': 4},
                {'title': 'Check smoke detector batteries', 'item_type': 'check', 'order': 5},
                {'title': 'Inspect windows and locks', 'item_type': 'check', 'order': 6},
                {'title': 'Note required repairs or part replacements', 'item_type': 'text_input', 'order': 7},
                {'title': 'Update inventory levels', 'item_type': 'check', 'order': 8},
            ]
            
            for item_data in maintenance_items:
                ChecklistItem.objects.create(
                    template=maintenance_template,
                    **item_data
                )
            
            self.stdout.write(f'Created maintenance checklist template with {len(maintenance_items)} items')

        # Laundry Checklist Template
        laundry_template, created = ChecklistTemplate.objects.get_or_create(
            name='Laundry Service Workflow',
            task_type='laundry',
            defaults={
                'description': 'Complete laundry pick-up, processing, and delivery',
                'created_by': admin_user,
            }
        )
        
        if created:
            laundry_items = [
                {'title': 'Count and log linens picked up', 'item_type': 'number_input', 'order': 1},
                {'title': 'Photo of dirty linens', 'item_type': 'photo_required', 'order': 2},
                {'title': 'Note any stains or damage', 'item_type': 'text_input', 'order': 3},
                {'title': 'Wash and dry completed', 'item_type': 'blocking', 'order': 4},
                {'title': 'Quality check completed', 'item_type': 'blocking', 'order': 5},
                {'title': 'Count and log clean linens delivered', 'item_type': 'number_input', 'order': 6},
                {'title': 'Photo of clean linens delivered', 'item_type': 'photo_required', 'order': 7},
                {'title': 'Restock linen closet', 'item_type': 'check', 'order': 8},
            ]
            
            for item_data in laundry_items:
                ChecklistItem.objects.create(
                    template=laundry_template,
                    **item_data
                )
            
            self.stdout.write(f'Created laundry checklist template with {len(laundry_items)} items')

    def create_inventory_system(self, admin_user):
        """Create inventory categories and items."""
        
        # Create Inventory Categories
        categories_data = [
            {'name': 'Cleaning Supplies', 'description': 'All cleaning products and tools', 'icon': '🧽'},
            {'name': 'Bathroom Amenities', 'description': 'Toiletries and bathroom supplies', 'icon': '🚿'},
            {'name': 'Kitchen Supplies', 'description': 'Kitchen consumables and tools', 'icon': '🍽️'},
            {'name': 'Maintenance Parts', 'description': 'Hardware and repair supplies', 'icon': '🔧'},
            {'name': 'Laundry Supplies', 'description': 'Detergents and fabric care', 'icon': '👕'},
            {'name': 'Pool & Spa', 'description': 'Pool chemicals and equipment', 'icon': '🏊'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = InventoryCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create Inventory Items
        items_data = [
            # Cleaning Supplies
            {'name': 'All-Purpose Cleaner', 'category': 'Cleaning Supplies', 'unit': 'bottle', 'estimated_cost': 4.99},
            {'name': 'Disinfectant Spray', 'category': 'Cleaning Supplies', 'unit': 'bottle', 'estimated_cost': 6.99},
            {'name': 'Vacuum Bags', 'category': 'Cleaning Supplies', 'unit': 'pack', 'estimated_cost': 12.99},
            {'name': 'Microfiber Cloths', 'category': 'Cleaning Supplies', 'unit': 'pack', 'estimated_cost': 15.99},
            {'name': 'Toilet Paper', 'category': 'Bathroom Amenities', 'unit': 'pack', 'estimated_cost': 8.99},
            
            # Bathroom Amenities
            {'name': 'Shampoo', 'category': 'Bathroom Amenities', 'unit': 'bottle', 'estimated_cost': 3.99},
            {'name': 'Conditioner', 'category': 'Bathroom Amenities', 'unit': 'bottle', 'estimated_cost': 3.99},
            {'name': 'Body Wash', 'category': 'Bathroom Amenities', 'unit': 'bottle', 'estimated_cost': 4.99},
            {'name': 'Towels - Bath', 'category': 'Bathroom Amenities', 'unit': 'each', 'estimated_cost': 25.99},
            {'name': 'Towels - Hand', 'category': 'Bathroom Amenities', 'unit': 'each', 'estimated_cost': 12.99},
            
            # Kitchen Supplies
            {'name': 'Dish Soap', 'category': 'Kitchen Supplies', 'unit': 'bottle', 'estimated_cost': 2.99},
            {'name': 'Paper Towels', 'category': 'Kitchen Supplies', 'unit': 'roll', 'estimated_cost': 1.99},
            {'name': 'Trash Bags', 'category': 'Kitchen Supplies', 'unit': 'box', 'estimated_cost': 11.99},
            {'name': 'Coffee Filters', 'category': 'Kitchen Supplies', 'unit': 'pack', 'estimated_cost': 4.99},
            
            # Maintenance Parts
            {'name': 'Light Bulbs - LED 60W', 'category': 'Maintenance Parts', 'unit': 'pack', 'estimated_cost': 9.99},
            {'name': 'HVAC Filters', 'category': 'Maintenance Parts', 'unit': 'each', 'estimated_cost': 15.99},
            {'name': 'Smoke Detector Batteries', 'category': 'Maintenance Parts', 'unit': 'pack', 'estimated_cost': 7.99},
            {'name': 'Plumbing Tape', 'category': 'Maintenance Parts', 'unit': 'roll', 'estimated_cost': 2.99},
            
            # Laundry Supplies
            {'name': 'Laundry Detergent', 'category': 'Laundry Supplies', 'unit': 'bottle', 'estimated_cost': 12.99},
            {'name': 'Fabric Softener', 'category': 'Laundry Supplies', 'unit': 'bottle', 'estimated_cost': 4.99},
            {'name': 'Bleach', 'category': 'Laundry Supplies', 'unit': 'bottle', 'estimated_cost': 3.99},
            
            # Pool & Spa
            {'name': 'Chlorine Tablets', 'category': 'Pool & Spa', 'unit': 'bag', 'estimated_cost': 29.99},
            {'name': 'Pool Test Strips', 'category': 'Pool & Spa', 'unit': 'pack', 'estimated_cost': 12.99},
            {'name': 'Pool Shock', 'category': 'Pool & Spa', 'unit': 'bag', 'estimated_cost': 19.99},
        ]
        
        properties = Property.objects.all()
        
        for item_data in items_data:
            category_name = item_data.pop('category')
            category = categories[category_name]
            
            item, created = InventoryItem.objects.get_or_create(
                name=item_data['name'],
                category=category,
                defaults=item_data
            )
            
            if created:
                # Create property inventory for each property with random stock levels
                import random
                for prop in properties:
                    par_level = random.randint(5, 20)
                    current_stock = random.randint(0, par_level * 2)
                    
                    PropertyInventory.objects.create(
                        property_ref=prop,
                        item=item,
                        current_stock=current_stock,
                        par_level=par_level,
                        max_level=par_level * 3,
                        storage_location=f"Storage Room {random.choice(['A', 'B', 'C'])}",
                        updated_by=admin_user
                    )
                
                self.stdout.write(f'Created inventory item: {item.name}')
        
        self.stdout.write(f'Created {len(items_data)} inventory items across {len(categories)} categories')
