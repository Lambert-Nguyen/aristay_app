"""
Management command to create sample tasks with checklists for different workflows.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import (
    Property, Task, ChecklistTemplate, TaskChecklist, ChecklistResponse,
    Booking, InventoryTransaction, PropertyInventory
)
from django.utils import timezone
import random


class Command(BaseCommand):
    help = 'Create sample tasks with checklists to demonstrate workflow specialization'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample tasks with specialized workflows...')
        
        # Get existing data
        admin_user = User.objects.get(username='admin')
        properties = list(Property.objects.all())
        
        if not properties:
            self.stdout.write(self.style.ERROR('No properties found. Run create_sample_mvp_data first.'))
            return
        
        # Create some bookings
        self.create_sample_bookings(properties, admin_user)
        
        # Create sample tasks with checklists
        self.create_cleaning_tasks(properties, admin_user)
        self.create_maintenance_tasks(properties, admin_user)
        self.create_laundry_tasks(properties, admin_user)
        
        self.stdout.write(self.style.SUCCESS('Sample specialized workflow tasks created!'))

    def create_sample_bookings(self, properties, admin_user):
        """Create sample bookings for task assignment."""
        
        bookings_created = 0
        for prop in properties:
            if not prop.bookings.exists():
                # Create 2-3 bookings per property
                for i in range(random.randint(2, 3)):
                    start_date = timezone.now() + timezone.timedelta(days=random.randint(-7, 30))
                    end_date = start_date + timezone.timedelta(days=random.randint(2, 7))
                    
                    booking = Booking.objects.create(
                        property=prop,
                        check_in_date=start_date,
                        check_out_date=end_date,
                        guest_name=f"Guest {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones'])}",
                        guest_contact=f"guest{i}@email.com",
                        status=random.choice(['upcoming', 'active', 'completed'])
                    )
                    bookings_created += 1
        
        self.stdout.write(f'Created {bookings_created} sample bookings')

    def create_cleaning_tasks(self, properties, admin_user):
        """Create cleaning tasks with attached checklists."""
        
        cleaning_template = ChecklistTemplate.objects.get(name='Standard Room Cleaning')
        
        for prop in properties:
            bookings = list(prop.bookings.all())
            if bookings:
                # Create 1-2 cleaning tasks per property
                for i in range(random.randint(1, 2)):
                    booking = random.choice(bookings)
                    
                    task = Task.objects.create(
                        task_type='cleaning',
                        title=f'Room Cleaning - {prop.name}',
                        description=f'Complete room cleaning for guest checkout/checkin at {prop.name}',
                        property=prop,
                        booking=booking,
                        status='pending',
                        created_by=admin_user,
                        due_date=booking.check_in_date - timezone.timedelta(hours=2)
                    )
                    
                    # Create checklist for this task
                    task_checklist = TaskChecklist.objects.create(
                        task=task,
                        template=cleaning_template
                    )
                    
                    # Create responses for all checklist items
                    for item in cleaning_template.items.all():
                        ChecklistResponse.objects.create(
                            checklist=task_checklist,
                            item=item,
                            is_completed=random.choice([True, False]) if item.item_type != 'blocking' else False
                        )
                    
                    self.stdout.write(f'Created cleaning task: {task.title}')

    def create_maintenance_tasks(self, properties, admin_user):
        """Create maintenance tasks with checklists."""
        
        maintenance_template = ChecklistTemplate.objects.get(name='Property Maintenance Inspection')
        
        for prop in properties:
            # Create 1 maintenance task per property
            task = Task.objects.create(
                task_type='maintenance',
                title=f'Monthly Maintenance - {prop.name}',
                description=f'Regular maintenance inspection and inventory check for {prop.name}',
                property=prop,
                status='pending',
                created_by=admin_user,
                due_date=timezone.now() + timezone.timedelta(days=random.randint(1, 15))
            )
            
            # Create checklist for this task
            task_checklist = TaskChecklist.objects.create(
                task=task,
                template=maintenance_template
            )
            
            # Create responses for all checklist items
            for item in maintenance_template.items.all():
                ChecklistResponse.objects.create(
                    checklist=task_checklist,
                    item=item,
                    is_completed=random.choice([True, False])
                )
            
            # Create some sample inventory transactions for this task
            property_inventory_items = PropertyInventory.objects.filter(property_ref=prop)[:3]
            for inv_item in property_inventory_items:
                if random.choice([True, False]):  # 50% chance
                    InventoryTransaction.objects.create(
                        property_inventory=inv_item,
                        transaction_type=random.choice(['stock_in', 'stock_out', 'adjustment']),
                        quantity=random.randint(1, 5),
                        task=task,
                        notes=f'Maintenance task inventory update',
                        created_by=admin_user
                    )
            
            self.stdout.write(f'Created maintenance task: {task.title}')

    def create_laundry_tasks(self, properties, admin_user):
        """Create laundry tasks with workflow checklists."""
        
        laundry_template = ChecklistTemplate.objects.get(name='Laundry Service Workflow')
        
        for prop in properties:
            bookings = list(prop.bookings.filter(status='upcoming'))
            if bookings:
                # Create 1 laundry task per property for upcoming bookings
                booking = random.choice(bookings)
                
                task = Task.objects.create(
                    task_type='laundry',
                    title=f'Laundry Service - {prop.name}',
                    description=f'Complete laundry service for upcoming guest at {prop.name}',
                    property=prop,
                    booking=booking,
                    status='pending', 
                    created_by=admin_user,
                    due_date=booking.check_in_date - timezone.timedelta(hours=6)
                )
                
                # Create checklist for this task
                task_checklist = TaskChecklist.objects.create(
                    task=task,
                    template=laundry_template
                )
                
                # Create responses for all checklist items
                for item in laundry_template.items.all():
                    response = ChecklistResponse.objects.create(
                        checklist=task_checklist,
                        item=item,
                        is_completed=random.choice([True, False])
                    )
                    
                    # Add sample data for number inputs
                    if item.item_type == 'number_input':
                        response.number_response = random.randint(5, 20)
                        response.save()
                    
                    # Add sample text for text inputs
                    if item.item_type == 'text_input' and random.choice([True, False]):
                        response.text_response = random.choice([
                            'Small stain on pillowcase - treated',
                            'All items in good condition',
                            'Minor wear on towel corners',
                            'No issues noted'
                        ])
                        response.save()
                
                self.stdout.write(f'Created laundry task: {task.title}')
