#!/usr/bin/env python
"""
Populate checklist items for existing templates and assign checklists to tasks.

Templates targeted (by name):
- Standard Cleaning Checklist
- Property Maintenance Checklist
- Laundry Management Checklist
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import transaction
from api.models import (
    ChecklistTemplate, ChecklistItem, Task, TaskChecklist, ChecklistResponse
)


def ensure_items_for_template(template: ChecklistTemplate):
    if template.items.exists():
        print(f"ℹ️ Template '{template.name}' already has {template.items.count()} items")
        return

    print(f"✅ Creating items for '{template.name}' ({template.task_type})")
    items_by_type = {
        'cleaning': [
            ("Bathroom Cleaning", "check", True, "Clean toilet, sink, mirror, and shower", "bathroom"),
            ("Bathroom Photos", "photo_required", True, "Take before/after photos of bathroom", "bathroom"),
            ("Bedroom Cleaning", "check", True, "Make bed, vacuum, dust surfaces", "bedroom"),
            ("Bedroom Photos", "photo_required", True, "Take before/after photos of bedroom", "bedroom"),
            ("Kitchen Cleaning", "check", True, "Clean countertops, sink, and appliances", "kitchen"),
            ("Kitchen Photos", "photo_required", True, "Take before/after photos of kitchen", "kitchen"),
            ("Living Room Cleaning", "check", True, "Vacuum, dust, organize furniture", "living"),
            ("Living Room Photos", "photo_required", True, "Take before/after photos of living room", "living"),
            ("Final Inspection", "check", True, "Walk entire property for quality check", ""),
            ("Completion Notes", "text_input", False, "Add any additional notes or issues found", ""),
        ],
        'maintenance': [
            ("HVAC Check", "check", True, "Test heating and cooling systems", "hvac"),
            ("HVAC Photos", "photo_required", True, "Take photos of HVAC units and thermostats", "hvac"),
            ("Plumbing Check", "check", True, "Check faucets, toilets, and water pressure", "plumbing"),
            ("Plumbing Photos", "photo_required", True, "Take photos of any plumbing issues", "plumbing"),
            ("Electrical Check", "check", True, "Test outlets, switches, and lighting", "electrical"),
            ("Electrical Photos", "photo_required", True, "Take photos of electrical panels and outlets", "electrical"),
            ("Safety Check", "check", True, "Check smoke detectors, locks, and security", "safety"),
            ("Safety Photos", "photo_required", True, "Take photos of safety equipment", "safety"),
            ("Exterior Check", "check", True, "Inspect exterior walls, windows, and doors", "exterior"),
            ("Exterior Photos", "photo_required", True, "Take photos of exterior condition", "exterior"),
            ("Maintenance Notes", "text_input", False, "Document any issues or repairs needed", ""),
        ],
        'laundry': [
            ("Linen Count In", "number_input", True, "Count all linens being collected", ""),
            ("Linen Count Photos", "photo_required", True, "Take photos of linens being collected", ""),
            ("Quality Inspection", "check", True, "Check for stains, tears, or damage", ""),
            ("Quality Photos", "photo_required", True, "Take photos of any damaged items", ""),
            ("Wash Cycle", "check", True, "Complete wash cycle with appropriate settings", ""),
            ("Dry Cycle", "check", True, "Complete dry cycle and check for proper drying", ""),
            ("Folding & Sorting", "check", True, "Fold and sort linens by type and size", ""),
            ("Folding Photos", "photo_required", True, "Take photos of folded linens", ""),
            ("Storage", "check", True, "Store linens in appropriate locations", ""),
            ("Storage Photos", "photo_required", True, "Take photos of storage areas", ""),
            ("Laundry Notes", "text_input", False, "Add any notes about laundry condition or issues", ""),
        ],
    }

    payload = items_by_type.get(template.task_type, [])
    bulk = []
    order = 0
    for title, item_type, is_required, description, room in payload:
        bulk.append(ChecklistItem(
            template=template,
            title=title,
            item_type=item_type,
            is_required=is_required,
            description=description,
            order=order,
            room_type=room or ''
        ))
        order += 1
    if bulk:
        ChecklistItem.objects.bulk_create(bulk)
        print(f"   → Added {len(bulk)} items")


def ensure_task_checklists():
    mapping = {}
    for name, ttype in [
        ("Standard Cleaning Checklist", 'cleaning'),
        ("Property Maintenance Checklist", 'maintenance'),
        ("Laundry Management Checklist", 'laundry'),
    ]:
        try:
            mapping[ttype] = ChecklistTemplate.objects.get(name=name, task_type=ttype)
        except ChecklistTemplate.DoesNotExist:
            print(f"⚠️ Missing template: {name} ({ttype})")

    total_assigned = 0
    for ttype, template in mapping.items():
        if not template:
            continue
        tasks = Task.objects.filter(task_type=ttype, is_deleted=False)
        print(f"Processing {tasks.count()} {ttype} tasks for template '{template.name}'")
        for task in tasks:
            if hasattr(task, 'checklist'):
                continue
            with transaction.atomic():
                cl = TaskChecklist.objects.create(task=task, template=template)
                items = template.items.all()
                ChecklistResponse.objects.bulk_create([
                    ChecklistResponse(checklist=cl, item=item) for item in items
                ])
                total_assigned += 1
                print(f"   → Assigned checklist to task #{task.id} - {task.title}")
    print(f"✅ Assigned {total_assigned} task checklists")


def main():
    # Ensure items exist for the three templates
    for name in [
        "Standard Cleaning Checklist",
        "Property Maintenance Checklist",
        "Laundry Management Checklist",
    ]:
        try:
            tpl = ChecklistTemplate.objects.get(name=name)
            ensure_items_for_template(tpl)
        except ChecklistTemplate.DoesNotExist:
            print(f"⚠️ Template not found: {name}")

    # Assign to tasks and create responses
    ensure_task_checklists()


if __name__ == '__main__':
    main()


