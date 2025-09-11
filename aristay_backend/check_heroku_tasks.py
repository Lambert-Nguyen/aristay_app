#!/usr/bin/env python
"""
Script to check tasks on Heroku and populate with demo checklists
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Task, ChecklistTemplate, ChecklistItem, TaskChecklist, Property
from django.contrib.auth.models import User

def check_current_tasks():
    print("=== CURRENT TASKS ON HEROKU ===")
    tasks = Task.objects.filter(is_deleted=False).order_by('-created_at')
    print(f'Total tasks: {tasks.count()}')
    
    for task in tasks[:10]:  # Show first 10
        print(f'ID: {task.id} | Title: {task.title} | Status: {task.status} | Type: {task.task_type} | Property: {task.property_ref}')
    
    print("\n=== CHECKLIST TEMPLATES ===")
    templates = ChecklistTemplate.objects.all()
    print(f'Total templates: {templates.count()}')
    for template in templates:
        print(f'ID: {template.id} | Name: {template.name} | Task Type: {template.task_type} | Items: {template.items.count()}')
    
    print("\n=== TASK CHECKLISTS ===")
    task_checklists = TaskChecklist.objects.all()
    print(f'Total task checklists: {task_checklists.count()}')
    for tc in task_checklists[:5]:
        print(f'Task: {tc.task.title} | Template: {tc.template.name} | Progress: {tc.get_completion_percentage()}%')
    
    return tasks, templates

def create_demo_checklist_templates():
    print("\n=== CREATING DEMO CHECKLIST TEMPLATES ===")
    
    # Get or create a demo user for created_by
    user, _ = User.objects.get_or_create(
        username='demo_user',
        defaults={
            'email': 'demo@aristay.com',
            'first_name': 'Demo',
            'last_name': 'User'
        }
    )
    
    # Cleaning Checklist Template
    cleaning_template, created = ChecklistTemplate.objects.get_or_create(
        name="Standard Cleaning Checklist",
        task_type="cleaning",
        defaults={
            'description': 'Comprehensive cleaning checklist for property maintenance',
            'created_by': user
        }
    )
    
    if created:
        print(f"✅ Created cleaning template: {cleaning_template.name}")
        
        # Add cleaning checklist items
        cleaning_items = [
            ("Bathroom Cleaning", "Check items", True, "Clean toilet, sink, mirror, and shower"),
            ("Bathroom Photos", "Photo required", True, "Take before/after photos of bathroom"),
            ("Bedroom Cleaning", "Check items", True, "Make bed, vacuum, dust surfaces"),
            ("Bedroom Photos", "Photo required", True, "Take before/after photos of bedroom"),
            ("Kitchen Cleaning", "Check items", True, "Clean countertops, sink, and appliances"),
            ("Kitchen Photos", "Photo required", True, "Take before/after photos of kitchen"),
            ("Living Room Cleaning", "Check items", True, "Vacuum, dust, organize furniture"),
            ("Living Room Photos", "Photo required", True, "Take before/after photos of living room"),
            ("Final Inspection", "Check items", True, "Walk through entire property for quality check"),
            ("Completion Notes", "Text input", False, "Add any additional notes or issues found")
        ]
        
        for item_text, item_type, is_required, description in cleaning_items:
            ChecklistItem.objects.create(
                template=cleaning_template,
                text=item_text,
                item_type=item_type,
                is_required=is_required,
                description=description
            )
        
        print(f"✅ Added {len(cleaning_items)} items to cleaning template")
    else:
        print(f"ℹ️ Cleaning template already exists: {cleaning_template.name}")
    
    # Maintenance Checklist Template
    maintenance_template, created = ChecklistTemplate.objects.get_or_create(
        name="Property Maintenance Checklist",
        task_type="maintenance",
        defaults={
            'description': 'Comprehensive maintenance checklist for property upkeep',
            'created_by': user
        }
    )
    
    if created:
        print(f"✅ Created maintenance template: {maintenance_template.name}")
        
        # Add maintenance checklist items
        maintenance_items = [
            ("HVAC Check", "Check items", True, "Test heating and cooling systems"),
            ("HVAC Photos", "Photo required", True, "Take photos of HVAC units and thermostats"),
            ("Plumbing Check", "Check items", True, "Check faucets, toilets, and water pressure"),
            ("Plumbing Photos", "Photo required", True, "Take photos of any plumbing issues"),
            ("Electrical Check", "Check items", True, "Test outlets, switches, and lighting"),
            ("Electrical Photos", "Photo required", True, "Take photos of electrical panels and outlets"),
            ("Safety Check", "Check items", True, "Check smoke detectors, locks, and security"),
            ("Safety Photos", "Photo required", True, "Take photos of safety equipment"),
            ("Exterior Check", "Check items", True, "Inspect exterior walls, windows, and doors"),
            ("Exterior Photos", "Photo required", True, "Take photos of exterior condition"),
            ("Maintenance Notes", "Text input", False, "Document any issues or repairs needed")
        ]
        
        for item_text, item_type, is_required, description in maintenance_items:
            ChecklistItem.objects.create(
                template=maintenance_template,
                text=item_text,
                item_type=item_type,
                is_required=is_required,
                description=description
            )
        
        print(f"✅ Added {len(maintenance_items)} items to maintenance template")
    else:
        print(f"ℹ️ Maintenance template already exists: {maintenance_template.name}")
    
    # Laundry Checklist Template
    laundry_template, created = ChecklistTemplate.objects.get_or_create(
        name="Laundry Management Checklist",
        task_type="laundry",
        defaults={
            'description': 'Comprehensive laundry checklist for linen management',
            'created_by': user
        }
    )
    
    if created:
        print(f"✅ Created laundry template: {laundry_template.name}")
        
        # Add laundry checklist items
        laundry_items = [
            ("Linen Count In", "Number input", True, "Count all linens being collected"),
            ("Linen Count Photos", "Photo required", True, "Take photos of linens being collected"),
            ("Quality Inspection", "Check items", True, "Check for stains, tears, or damage"),
            ("Quality Photos", "Photo required", True, "Take photos of any damaged items"),
            ("Wash Cycle", "Check items", True, "Complete wash cycle with appropriate settings"),
            ("Dry Cycle", "Check items", True, "Complete dry cycle and check for proper drying"),
            ("Folding & Sorting", "Check items", True, "Fold and sort linens by type and size"),
            ("Folding Photos", "Photo required", True, "Take photos of folded linens"),
            ("Storage", "Check items", True, "Store linens in appropriate locations"),
            ("Storage Photos", "Photo required", True, "Take photos of storage areas"),
            ("Laundry Notes", "Text input", False, "Add any notes about laundry condition or issues")
        ]
        
        for item_text, item_type, is_required, description in laundry_items:
            ChecklistItem.objects.create(
                template=laundry_template,
                text=item_text,
                item_type=item_type,
                is_required=is_required,
                description=description
            )
        
        print(f"✅ Added {len(laundry_items)} items to laundry template")
    else:
        print(f"ℹ️ Laundry template already exists: {laundry_template.name}")
    
    return cleaning_template, maintenance_template, laundry_template

def assign_checklists_to_tasks(tasks, cleaning_template, maintenance_template, laundry_template):
    print("\n=== ASSIGNING CHECKLISTS TO TASKS ===")
    
    assigned_count = 0
    
    for task in tasks:
        # Skip if task already has a checklist
        if TaskChecklist.objects.filter(task=task).exists():
            continue
        
        # Assign appropriate template based on task type
        template = None
        if task.task_type == 'cleaning':
            template = cleaning_template
        elif task.task_type == 'maintenance':
            template = maintenance_template
        elif task.task_type == 'laundry':
            template = laundry_template
        else:
            # Default to cleaning for other types
            template = cleaning_template
        
        if template:
            task_checklist = TaskChecklist.objects.create(
                task=task,
                template=template
            )
            assigned_count += 1
            print(f"✅ Assigned {template.name} to task: {task.title}")
    
    print(f"\n✅ Assigned checklists to {assigned_count} tasks")

def create_demo_tasks():
    print("\n=== CREATING DEMO TASKS ===")
    
    # Get or create a property
    property_obj, created = Property.objects.get_or_create(
        name="Demo Property - 123 Main St",
        defaults={
            'address': '123 Main Street, Tampa, FL 33601',
            'property_type': 'apartment',
            'description': 'Demo property for customer presentation'
        }
    )
    
    if created:
        print(f"✅ Created demo property: {property_obj.name}")
    else:
        print(f"ℹ️ Using existing property: {property_obj.name}")
    
    # Get or create a demo user
    user, created = User.objects.get_or_create(
        username='demo_user',
        defaults={
            'email': 'demo@aristay.com',
            'first_name': 'Demo',
            'last_name': 'User'
        }
    )
    
    if created:
        print(f"✅ Created demo user: {user.username}")
    else:
        print(f"ℹ️ Using existing user: {user.username}")
    
    # Create demo tasks
    demo_tasks = [
        {
            'title': 'Weekly Apartment Cleaning',
            'description': 'Complete weekly cleaning of apartment unit',
            'task_type': 'cleaning',
            'status': 'pending',
            'priority': 'medium'
        },
        {
            'title': 'Monthly Maintenance Check',
            'description': 'Perform monthly maintenance inspection',
            'task_type': 'maintenance',
            'status': 'pending',
            'priority': 'high'
        },
        {
            'title': 'Linen Laundry Service',
            'description': 'Process and clean all property linens',
            'task_type': 'laundry',
            'status': 'pending',
            'priority': 'medium'
        },
        {
            'title': 'Deep Clean Bathroom',
            'description': 'Thorough cleaning of bathroom facilities',
            'task_type': 'cleaning',
            'status': 'in-progress',
            'priority': 'high'
        },
        {
            'title': 'HVAC System Inspection',
            'description': 'Check and maintain HVAC systems',
            'task_type': 'maintenance',
            'status': 'pending',
            'priority': 'high'
        }
    ]
    
    created_tasks = []
    for task_data in demo_tasks:
        task, created = Task.objects.get_or_create(
            title=task_data['title'],
            property_ref=property_obj,
            defaults={
                'description': task_data['description'],
                'task_type': task_data['task_type'],
                'status': task_data['status'],
                'priority': task_data['priority'],
                'created_by': user,
                'assigned_to': user
            }
        )
        
        if created:
            created_tasks.append(task)
            print(f"✅ Created task: {task.title}")
        else:
            print(f"ℹ️ Task already exists: {task.title}")
    
    return created_tasks

def main():
    print("🚀 ARISTAY HEROKU TASK & CHECKLIST DEMO SETUP")
    print("=" * 50)
    
    # Check current state
    tasks, templates = check_current_tasks()
    
    # Create demo tasks if needed
    if tasks.count() < 5:
        demo_tasks = create_demo_tasks()
        tasks = Task.objects.filter(is_deleted=False).order_by('-created_at')
    
    # Create checklist templates
    cleaning_template, maintenance_template, laundry_template = create_demo_checklist_templates()
    
    # Assign checklists to tasks
    assign_checklists_to_tasks(tasks, cleaning_template, maintenance_template, laundry_template)
    
    # Final summary
    print("\n=== FINAL SUMMARY ===")
    print(f"Total tasks: {Task.objects.filter(is_deleted=False).count()}")
    print(f"Total templates: {ChecklistTemplate.objects.count()}")
    print(f"Total task checklists: {TaskChecklist.objects.count()}")
    
    print("\n✅ Demo setup complete! Ready for customer presentation.")

if __name__ == '__main__':
    main()
