"""
Web views for checklist management
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
import json

from api.models import ChecklistTemplate, ChecklistItem, Task, TaskChecklist, ChecklistResponse
from django.contrib.auth.decorators import user_passes_test
from api.authz import has_role

def is_staff_or_manager(user):
    """Check if user is staff or manager"""
    return user.is_authenticated and (user.is_staff or has_role(user, 'manager'))


@login_required
@user_passes_test(is_staff_or_manager)
def checklist_templates(request):
    """List all checklist templates"""
    templates = ChecklistTemplate.objects.filter(is_active=True).order_by('task_type', 'name')
    
    # Group templates by task type
    templates_by_type = {}
    for template in templates:
        if template.task_type not in templates_by_type:
            templates_by_type[template.task_type] = []
        templates_by_type[template.task_type].append(template)
    
    context = {
        'templates_by_type': templates_by_type,
        'title': 'Checklist Templates',
    }
    
    return render(request, 'staff/checklist_templates.html', context)


@login_required
@user_passes_test(is_staff_or_manager)
def create_checklist_template(request):
    """Create a new checklist template"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create template
            template = ChecklistTemplate.objects.create(
                name=data['name'],
                task_type=data['task_type'],
                description=data.get('description', ''),
                is_active=True,
                created_by=request.user
            )
            
            # Create items
            for item_data in data.get('items', []):
                ChecklistItem.objects.create(
                    template=template,
                    title=item_data['title'],
                    description=item_data.get('description', ''),
                    item_type=item_data.get('item_type', 'check'),
                    is_required=item_data.get('is_required', True),
                    order=item_data.get('order', 0),
                    room_type=item_data.get('room_type', 'General')
                )
            
            return JsonResponse({
                'success': True,
                'template_id': template.id,
                'message': f'Template "{template.name}" created successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    # GET request - show form
    context = {
        'title': 'Create Checklist Template',
        'task_types': Task.TASK_TYPE_CHOICES,
        'item_types': ChecklistItem.ITEM_TYPE_CHOICES,
        'room_types': ['General', 'bathroom', 'bedroom', 'kitchen', 'living_room'],
    }
    
    return render(request, 'staff/create_checklist_template.html', context)


@login_required
@user_passes_test(is_staff_or_manager)
def assign_checklist_to_task(request, task_id):
    """Assign a checklist template to a specific task"""
    task = get_object_or_404(Task, id=task_id, is_deleted=False)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            template_id = data.get('template_id')
            
            if not template_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Template ID is required'
                }, status=400)
            
            template = get_object_or_404(ChecklistTemplate, id=template_id, is_active=True)
            
            with transaction.atomic():
                # Create task checklist
                task_checklist, created = TaskChecklist.objects.get_or_create(
                    task=task,
                    template=template,
                    defaults={
                        'started_at': None,
                        'completed_at': None,
                        'completed_by': None,
                    }
                )
                
                if not created:
                    return JsonResponse({
                        'success': False,
                        'error': 'Task already has a checklist assigned'
                    }, status=400)
                
                # Create responses for all checklist items
                for item in template.items.all():
                    ChecklistResponse.objects.create(
                        checklist=task_checklist,
                        item=item,
                        is_completed=False,
                        text_response='',
                        number_response=None,
                        completed_at=None,
                        completed_by=None,
                        notes='',
                    )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Checklist "{template.name}" assigned to task successfully!'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    # GET request - show assignment form
    available_templates = ChecklistTemplate.objects.filter(
        task_type=task.task_type,
        is_active=True
    ).order_by('name')
    
    context = {
        'task': task,
        'available_templates': available_templates,
        'title': f'Assign Checklist to {task.title}',
    }
    
    return render(request, 'staff/assign_checklist.html', context)


@login_required
@user_passes_test(is_staff_or_manager)
def quick_assign_checklists(request):
    """Quickly assign checklists to multiple tasks"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_ids = data.get('task_ids', [])
            template_id = data.get('template_id')
            
            if not task_ids or not template_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Task IDs and Template ID are required'
                }, status=400)
            
            template = get_object_or_404(ChecklistTemplate, id=template_id, is_active=True)
            assigned_count = 0
            
            with transaction.atomic():
                for task_id in task_ids:
                    try:
                        task = Task.objects.get(id=task_id, is_deleted=False)
                        
                        # Create task checklist
                        task_checklist, created = TaskChecklist.objects.get_or_create(
                            task=task,
                            template=template,
                            defaults={
                                'started_at': None,
                                'completed_at': None,
                                'completed_by': None,
                            }
                        )
                        
                        if created:
                            # Create responses for all checklist items
                            for item in template.items.all():
                                ChecklistResponse.objects.create(
                                    checklist=task_checklist,
                                    item=item,
                                    is_completed=False,
                                    text_response='',
                                    number_response=None,
                                    completed_at=None,
                                    completed_by=None,
                                    notes='',
                                )
                            assigned_count += 1
                            
                    except Task.DoesNotExist:
                        continue
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully assigned checklist to {assigned_count} tasks!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    # GET request - show form
    tasks_without_checklists = Task.objects.filter(
        is_deleted=False,
        checklist__isnull=True
    ).order_by('task_type', 'title')
    
    templates = ChecklistTemplate.objects.filter(is_active=True).order_by('task_type', 'name')
    
    context = {
        'tasks_without_checklists': tasks_without_checklists,
        'templates': templates,
        'title': 'Quick Assign Checklists',
    }
    
    return render(request, 'staff/quick_assign_checklists.html', context)
