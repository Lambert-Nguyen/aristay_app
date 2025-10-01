"""
Staff Portal Views - Role-based interfaces for different staff types.

This module provides specialized dashboard views and functionality for different 
categories of staff users including cleaning, maintenance, laundry, and lawn/pool teams.
Each dashboard is tailored to the specific workflows and needs of that department.

Key Features:
- Department-specific task lists and workflows
- Real-time task status updates
- Photo upload and management for task documentation
- Inventory lookup for maintenance staff
- Lost & found item management

Authorization:
- Uses centralized AuthzHelper for consistent permission checking
- Supports both role-based and permission-based access control
- Uses Profile.role for all business permission checks
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count, Prefetch, F
from django.core.paginator import Paginator
from django.db import transaction
from django.urls import reverse
from django.forms import ModelForm, CharField, Textarea, Select, DateInput, DateTimeInput
from django.core.exceptions import ValidationError
from datetime import timedelta
import json
import logging

# Set up logging
logger = logging.getLogger(__name__)


def get_team_tasks(request, task_type):
    """Get team tasks based on user permissions and task type."""
    try:
        profile = request.user.profile
        can_view_team_tasks = profile.can_view_team_tasks
    except Profile.DoesNotExist:
        can_view_team_tasks = True  # Default for users without profile
    
    if can_view_team_tasks:
        # Show all tasks of this type (team view)
        return Task.objects.filter(
            task_type=task_type,
            status__in=['pending', 'in-progress']
        ).select_related('property_ref', 'booking', 'assigned_to')
    else:
        # Show only assigned tasks (individual view)
        return Task.objects.filter(
            assigned_to=request.user,
            task_type=task_type,
            status__in=['pending', 'in-progress']
        ).select_related('property_ref', 'booking')

from .models import (
    Task, Property, TaskChecklist, ChecklistResponse, ChecklistPhoto, TaskImage,
    PropertyInventory, InventoryTransaction, LostFoundItem, Profile,
    Booking, TASK_TYPE_CHOICES, User
)
from .serializers import TaskSerializer
from .authz import AuthzHelper, can_edit_task, can_view_task
from .decorators import staff_or_perm


@login_required
def staff_dashboard(request):
    """Main staff dashboard with overview and quick actions."""
    
    logger.info(f"Staff dashboard accessed by user: {request.user.username}")
    
    # Get user role
    try:
        profile = request.user.profile
        user_role = profile.role
        logger.debug(f"User {request.user.username} has role: {user_role}")
    except Profile.DoesNotExist:
        user_role = 'staff'
        logger.warning(f"User {request.user.username} has no profile, defaulting to staff role")
    
    # Determine scope: managers and superusers see all tasks; staff see only assigned
    try:
        profile = request.user.profile
        is_manager = getattr(profile, 'role', '') == 'manager'
        # Only users explicitly granted team view can see all tasks
        can_view_team = bool(getattr(profile, 'can_view_team_tasks', False))
    except Profile.DoesNotExist:
        # No profile → treat as regular staff
        is_manager = False
        can_view_team = False

    if request.user.is_superuser or is_manager or can_view_team:
        scoped_tasks = Task.objects.all()
    else:
        scoped_tasks = Task.objects.filter(assigned_to=request.user)

    # Get user's task summary (scoped)
    total_tasks = scoped_tasks.count()
    
    task_counts = {
        'pending': scoped_tasks.filter(status='pending').count(),
        'in-progress': scoped_tasks.filter(status='in-progress').count(),
        'completed': scoped_tasks.filter(status='completed').count(),
        'overdue': scoped_tasks.filter(
            status__in=['pending', 'in-progress'],
            due_date__lt=timezone.now()
        ).count()
    }
    
    logger.debug(f"User {request.user.username} has {total_tasks} total tasks: {task_counts}")
    
    # Get recent tasks
    recent_tasks = scoped_tasks.select_related('property_ref', 'booking').order_by('-created_at')[:5]
    
    # Get properties user has access to using centralized authorization
    from .authz import AuthzHelper
    accessible_properties = AuthzHelper.get_accessible_properties(request.user)[:5]
    
    context = {
        'user_role': user_role,
        'total_tasks': total_tasks,
        'task_counts': task_counts,
        'recent_tasks': recent_tasks,
        'accessible_properties': accessible_properties,
        'user': request.user,  # Add user to context
    }
    
    logger.info(f"Staff dashboard rendered successfully for user: {request.user.username}")
    return render(request, 'staff/dashboard.html', context)


@login_required
def cleaning_dashboard(request):
    """Specialized dashboard for cleaning staff."""
    
    # Get team cleaning tasks (all team members)
    team_tasks = get_team_tasks(request, 'cleaning').prefetch_related('checklist__responses')
    
    # Get today's tasks
    today = timezone.now().date()
    today_tasks = team_tasks.filter(due_date__date=today)
    
    # Get upcoming tasks (next 7 days)
    upcoming_tasks = team_tasks.filter(
        due_date__date__gt=today,
        due_date__date__lte=today + timedelta(days=7)
    )
    
    # Get checklist progress
    tasks_with_progress = []
    for task in team_tasks:
        try:
            checklist = task.checklist
            progress = checklist.completion_percentage
        except:
            progress = 0
        
        tasks_with_progress.append({
            'task': task,
            'progress': progress,
            'checklist': getattr(task, 'checklist', None)
        })
    
    context = {
        'user_role': 'Cleaning Staff',
        'assigned_tasks': team_tasks,  # Now shows team tasks
        'today_tasks': today_tasks,
        'upcoming_tasks': upcoming_tasks,
        'tasks_with_progress': tasks_with_progress,
        'total_assigned': team_tasks.count(),
        'user': request.user,  # Add user to context
    }
    
    return render(request, 'staff/cleaning_dashboard.html', context)


@login_required
def maintenance_dashboard(request):
    """Specialized dashboard for maintenance staff."""
    
    # Get team maintenance tasks (all team members)
    team_tasks = get_team_tasks(request, 'maintenance')
    
    # Get low-stock inventory items across properties
    low_stock_items = PropertyInventory.objects.filter(
        current_stock__lte=F('par_level')
    ).select_related('property_ref', 'item', 'item__category')[:10]
    
    # Get recent inventory transactions
    recent_transactions = InventoryTransaction.objects.filter(
        created_by=request.user
    ).select_related(
        'property_inventory__property_ref', 
        'property_inventory__item'
    ).order_by('-created_at')[:10]
    
    # Get maintenance tasks by priority (overdue first)
    now = timezone.now()
    today = now.date()
    overdue_tasks = team_tasks.filter(due_date__lt=now)
    today_tasks = team_tasks.filter(due_date__date=today)
    
    context = {
        'user_role': 'Maintenance Staff',
        'assigned_tasks': team_tasks,  # Now shows team tasks
        'overdue_tasks': overdue_tasks,
        'today_tasks': today_tasks,
        'low_stock_items': low_stock_items,
        'recent_transactions': recent_transactions,
        'total_assigned': team_tasks.count(),
        'user': request.user,  # Add user to context
    }
    
    return render(request, 'staff/maintenance_dashboard.html', context)


@login_required
def laundry_dashboard(request):
    """Specialized dashboard for laundry staff."""
    
    # Get team laundry tasks (all team members)
    team_tasks = get_team_tasks(request, 'laundry')
    
    # Organize by workflow stage based on task status/progress
    pickup_tasks = team_tasks.filter(status='pending')
    processing_tasks = team_tasks.filter(status='in-progress')
    
    # Get linen inventory items
    linen_items = PropertyInventory.objects.filter(
        item__category__name='Bathroom Amenities',
        item__name__icontains='towel'
    ).select_related('property_ref', 'item')
    
    context = {
        'user_role': 'Laundry Staff',
        'pickup_tasks': pickup_tasks,
        'processing_tasks': processing_tasks,
        'linen_items': linen_items,
        'total_assigned': team_tasks.count(),
        'user': request.user,  # Add user to context
    }
    
    return render(request, 'staff/laundry_dashboard.html', context)


@login_required
def lawn_pool_dashboard(request):
    """Specialized dashboard for lawn/pool staff."""
    
    # Get team lawn/pool tasks (all team members)
    team_tasks = get_team_tasks(request, 'lawn_pool')
    
    # Get pool/spa inventory items
    pool_items = PropertyInventory.objects.filter(
        item__category__name='Pool & Spa'
    ).select_related('property_ref', 'item')
    
    # Group tasks by property for route planning
    tasks_by_property = {}
    for task in team_tasks:
        prop_name = task.property_ref.name if task.property_ref else 'Unassigned'
        if prop_name not in tasks_by_property:
            tasks_by_property[prop_name] = []
        tasks_by_property[prop_name].append(task)
    
    context = {
        'user_role': 'Lawn/Pool Staff',
        'assigned_tasks': team_tasks,  # Now shows team tasks
        'tasks_by_property': tasks_by_property,
        'pool_items': pool_items,
        'total_assigned': team_tasks.count(),
        'user': request.user,  # Add user to context
    }
    
    return render(request, 'staff/lawn_pool_dashboard.html', context)


@login_required
def task_detail(request, task_id):
    """Detailed task view with checklist interface."""
    
    task = get_object_or_404(
        Task.objects.select_related('property_ref', 'booking', 'assigned_to'),
        id=task_id
    )
    
    # Check if user can access this task
    if not can_view_task(request.user, task):
        messages.error(request, "You don't have permission to view this task.")
        return redirect('/api/staff/')
    
    # Get or lazily create checklist from an active template matching task type
    try:
        checklist = task.checklist
        # If checklist exists but has no responses, backfill from its template
        if checklist and not checklist.responses.exists():
            from django.db import transaction
            from .models import ChecklistItem, ChecklistResponse
            with transaction.atomic():
                items = ChecklistItem.objects.filter(template=checklist.template)
                ChecklistResponse.objects.bulk_create([
                    ChecklistResponse(checklist=checklist, item=item)
                for item in items], ignore_conflicts=True)
        responses = checklist.responses.select_related('item').prefetch_related('photos') if checklist else []
    except Exception:
        checklist = None
        responses = []

    if checklist is None:
        from django.db import transaction
        from .models import ChecklistTemplate, TaskChecklist, ChecklistItem, ChecklistResponse

        # Prefer an active template matching the task type
        template = (
            ChecklistTemplate.objects.filter(is_active=True, task_type=task.task_type)
            .order_by('-created_at')
            .first()
        )

        if template:
            # Create checklist and backfill responses atomically
            with transaction.atomic():
                items = ChecklistItem.objects.filter(template=template)
                if items.exists():
                    checklist = TaskChecklist.objects.create(task=task, template=template)
                    responses_to_create = [
                        ChecklistResponse(checklist=checklist, item=item)
                        for item in items
                    ]
                    ChecklistResponse.objects.bulk_create(responses_to_create, ignore_conflicts=True)
                    responses = checklist.responses.select_related('item').prefetch_related('photos')
    
    # Attach unified photos (TaskImage) per checklist response
    try:
        task_images = TaskImage.objects.filter(task=task).select_related('checklist_response')
        images_by_response = {}
        for img in task_images:
            rid = getattr(img.checklist_response, 'id', None)
            if rid:
                images_by_response.setdefault(rid, []).append(img)
    except Exception:
        images_by_response = {}

    # Group responses by room type for better organization
    responses_by_room = {}
    for response in responses:
        # Attach unified photos for template consumption
        setattr(response, 'unified_photos', images_by_response.get(response.id, []))
        room = response.item.room_type or 'General'
        if room not in responses_by_room:
            responses_by_room[room] = {
                'responses': [],
                'completed_count': 0,
                'total_count': 0
            }
        responses_by_room[room]['responses'].append(response)
        responses_by_room[room]['total_count'] += 1
        if response.is_completed:
            responses_by_room[room]['completed_count'] += 1
    
    # Check if user can approve photos
    can_approve_photos = (
        request.user.is_superuser or
        (hasattr(request.user, 'profile') and 
         (request.user.profile.role == 'manager' or 
          request.user.profile.has_permission('manage_files')))
    )
    
    context = {
        'task': task,
        'checklist': checklist,
        'responses_by_room': responses_by_room,
        'can_edit': can_edit_task(request.user, task),
        'can_approve_photos': can_approve_photos,
        'user': request.user,  # Add user to context
    }
    
    return render(request, 'staff/task_detail.html', context)


@login_required
@require_POST
def update_checklist_response(request, response_id):
    """Update a checklist response via AJAX."""
    
    try:
        response = get_object_or_404(ChecklistResponse, id=response_id)
        
        # Check permissions using centralized authorization
        if not can_edit_task(request.user, response.checklist.task):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        data = json.loads(request.body)
        
        # Update response fields
        if 'is_completed' in data:
            response.is_completed = data['is_completed']
            if response.is_completed:
                response.completed_at = timezone.now()
                response.completed_by = request.user
            else:
                response.completed_at = None
                response.completed_by = None
        
        if 'text_response' in data:
            response.text_response = data['text_response']
        
        if 'number_response' in data:
            response.number_response = data['number_response']
        
        if 'notes' in data:
            response.notes = data['notes']
        
        response.save()
        
        # Calculate overall progress
        checklist = response.checklist
        progress = checklist.completion_percentage
        
        return JsonResponse({
            'success': True,
            'progress': progress,
            'is_completed': response.is_completed
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def update_checklist_item(request, item_id):
    """Update a checklist item completion status via AJAX."""

    try:
        response = get_object_or_404(ChecklistResponse, id=item_id)

        # Check permissions using centralized authorization
        if not can_edit_task(request.user, response.checklist.task):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        data = json.loads(request.body)
        completed = data.get('completed', False)

        # Update response
        response.is_completed = completed
        if completed:
            response.completed_at = timezone.now()
            response.completed_by = request.user
        else:
            response.completed_at = None
            response.completed_by = None

        response.save()

        # Calculate overall progress
        checklist = response.checklist
        total_items = checklist.responses.count()
        completed_items = checklist.responses.filter(is_completed=True).count()
        percentage = int((completed_items / total_items) * 100) if total_items > 0 else 0

        return JsonResponse({
            'success': True,
            'completed': completed,
            'completed_at': response.completed_at.isoformat() if response.completed_at else None,
            'progress': {
                'completed': completed_items,
                'total': total_items,
                'percentage': percentage
            }
        })

    except Exception as e:
        logger.error(f"Error updating checklist item {item_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def my_tasks(request):
    """List of all tasks assigned to current user."""
    
    # Managers and superusers see all tasks; others see only assigned
    try:
        profile = request.user.profile
        is_manager = getattr(profile, 'role', '') == 'manager'
        # Only users explicitly granted team view can see all tasks
        can_view_team = bool(getattr(profile, 'can_view_team_tasks', False))
    except Profile.DoesNotExist:
        # No profile → treat as regular staff
        is_manager = False
        can_view_team = False

    if request.user.is_superuser or is_manager or can_view_team:
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(assigned_to=request.user)

    tasks = tasks.select_related('property_ref', 'booking').order_by('-due_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    # Filter by task type if provided
    type_filter = request.GET.get('type')
    if type_filter:
        tasks = tasks.filter(task_type=type_filter)
    
    # Search
    search = request.GET.get('q')
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(property_ref__name__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'search': search,
        'status_choices': Task.STATUS_CHOICES,
        'type_choices': TASK_TYPE_CHOICES,
        'user': request.user,  # Add user to context
    }
    
    return render(request, 'staff/my_tasks.html', context)


# Task Form for CRUD operations
class TaskForm(ModelForm):
    """Form for creating and editing tasks."""
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'task_type', 'status', 
            'due_date', 'assigned_to', 'property_ref', 'booking'
        ]
        widgets = {
            'description': Textarea(attrs={'rows': 4, 'cols': 40}),
            'due_date': DateTimeInput(attrs={'type': 'datetime-local'}),
            'task_type': Select(choices=TASK_TYPE_CHOICES),
            'status': Select(choices=Task.STATUS_CHOICES),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter properties to only show active ones
        self.fields['property_ref'].queryset = Property.objects.filter(is_deleted=False)
        
        # Filter users to only show staff members
        if user and not user.is_superuser:
            try:
                profile = user.profile
                if profile.role == 'manager':
                    # Managers can assign to all staff
                    self.fields['assigned_to'].queryset = User.objects.filter(
                        is_active=True, 
                        profile__isnull=False
                    ).exclude(profile__role='guest')
                else:
                    # Regular staff can only assign to themselves
                    self.fields['assigned_to'].queryset = User.objects.filter(id=user.id)
            except Profile.DoesNotExist:
                self.fields['assigned_to'].queryset = User.objects.filter(id=user.id)
        else:
            # Superusers can assign to all staff
            self.fields['assigned_to'].queryset = User.objects.filter(
                is_active=True, 
                profile__isnull=False
            ).exclude(profile__role='guest')
        
        # Set default assigned_to to current user
        if user and not self.instance.pk:
            self.fields['assigned_to'].initial = user


@login_required
def task_create(request):
    """Create a new task."""
    
    # Check if user can create tasks
    try:
        profile = request.user.profile
        can_create = (
            request.user.is_superuser or 
            profile.role == 'manager' or 
            profile.has_permission('add_task')
        )
    except Profile.DoesNotExist:
        can_create = request.user.is_superuser
    
    if not can_create:
        messages.error(request, "You don't have permission to create tasks.")
        return redirect('/api/staff/tasks/')
    
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            
            messages.success(request, f'Task "{task.title}" created successfully.')
            return redirect('staff-task-detail', task_id=task.id)
    else:
        form = TaskForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create New Task',
        'action': 'create',
        'user': request.user,
    }
    
    return render(request, 'staff/task_form.html', context)


@login_required
def task_edit(request, task_id):
    """Edit an existing task."""
    
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user can edit this task
    if not can_edit_task(request.user, task):
        messages.error(request, "You don't have permission to edit this task.")
        return redirect('staff-task-detail', task_id=task_id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Task "{task.title}" updated successfully.')
            return redirect('staff-task-detail', task_id=task.id)
    else:
        form = TaskForm(instance=task, user=request.user)
    
    context = {
        'form': form,
        'task': task,
        'title': f'Edit Task: {task.title}',
        'action': 'edit',
        'user': request.user,
    }
    
    return render(request, 'staff/task_form.html', context)


@login_required
@require_http_methods(["POST"])
def task_delete(request, task_id):
    """Delete a task."""
    
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user can delete this task
    try:
        profile = request.user.profile
        can_delete = (
            request.user.is_superuser or 
            profile.role == 'manager' or 
            profile.has_permission('delete_task') or
            task.created_by == request.user
        )
    except Profile.DoesNotExist:
        can_delete = request.user.is_superuser or task.created_by == request.user
    
    if not can_delete:
        messages.error(request, "You don't have permission to delete this task.")
        return redirect('staff-task-detail', task_id=task_id)
    
    task_title = task.title
    task.delete()
    
    messages.success(request, f'Task "{task_title}" deleted successfully.')
    return redirect('/api/staff/tasks/')


@login_required
def task_duplicate(request, task_id):
    """Duplicate an existing task."""
    
    original_task = get_object_or_404(Task, id=task_id)
    
    # Check if user can create tasks
    try:
        profile = request.user.profile
        can_create = (
            request.user.is_superuser or 
            profile.role == 'manager' or 
            profile.has_permission('add_task')
        )
    except Profile.DoesNotExist:
        can_create = request.user.is_superuser
    
    if not can_create:
        messages.error(request, "You don't have permission to create tasks.")
        return redirect('staff-task-detail', task_id=task_id)
    
    # Create duplicate
    duplicate_task = Task.objects.create(
        title=f"{original_task.title} (Copy)",
        description=original_task.description,
        task_type=original_task.task_type,
        status='pending',
        property_ref=original_task.property_ref,
        booking=original_task.booking,
        assigned_to=request.user,  # Assign to current user
        created_by=request.user,
        due_date=original_task.due_date,
    )
    
    messages.success(request, f'Task "{duplicate_task.title}" created successfully.')
    return redirect('staff-task-detail', task_id=duplicate_task.id)


@login_required
def inventory_lookup(request):
    """Inventory lookup interface for maintenance staff."""
    
    # Check if user should have inventory access using centralized authorization
    # Superusers, managers, users with inventory permissions, and maintenance department staff have access
    if not request.user.is_superuser:
        try:
            profile = request.user.profile
            user_role = profile.role
            
            # Allow managers, users with inventory permissions, and users in Maintenance department
            has_access = (
                user_role == 'manager' or
                profile.has_permission('view_inventory') or
                profile.is_in_department('Maintenance')
            )
            
            if not has_access:
                messages.error(request, "You don't have access to inventory management.")
                return redirect('/api/staff/')
        except:
            # If no profile, only allow superusers
            messages.error(request, "You don't have access to inventory management.")
            return redirect('/api/staff/')
    
    # Get property filter
    property_filter = request.GET.get('property')
    properties = Property.objects.all()
    
    # Get inventory items
    inventory = PropertyInventory.objects.select_related(
        'property_ref', 'item', 'item__category'
    ).order_by('property_ref__name', 'item__category__name', 'item__name')
    
    if property_filter:
        inventory = inventory.filter(property_ref_id=property_filter)
    
    # Group by category for better display
    inventory_by_category = {}
    for item in inventory:
        category = item.item.category.name
        if category not in inventory_by_category:
            inventory_by_category[category] = []
        inventory_by_category[category].append(item)
    
    context = {
        'inventory_by_category': inventory_by_category,
        'properties': properties,
        'selected_property': property_filter,
        'user': request.user,  # Add user to context
    }
    
    return render(request, 'staff/inventory_lookup.html', context)


@login_required
@require_POST
@staff_or_perm('manage_inventory')
@transaction.atomic
def log_inventory_transaction(request):
    """Log an inventory transaction (requires manage_inventory permission)."""
    
    try:
        data = json.loads(request.body)
        
        inventory_item = get_object_or_404(
            PropertyInventory,
            id=data['inventory_id']
        )
        
        # Use Decimal for precise calculations and atomic updates
        from decimal import Decimal
        from django.db.models import F
        qty = Decimal(str(data['quantity']))
        
        # Create transaction
        transaction = InventoryTransaction.objects.create(
            property_inventory=inventory_item,
            transaction_type=data['transaction_type'],
            quantity=qty,
            notes=data.get('notes', ''),
            task_id=data.get('task_id'),
            created_by=request.user
        )
        
        # Atomic stock update to avoid race conditions
        if data['transaction_type'] in ['stock_in', 'adjustment']:
            PropertyInventory.objects.filter(pk=inventory_item.pk).update(
                current_stock=F('current_stock') + qty, 
                updated_by=request.user
            )
        elif data['transaction_type'] in ['stock_out', 'damage']:
            PropertyInventory.objects.filter(pk=inventory_item.pk).update(
                current_stock=F('current_stock') - qty, 
                updated_by=request.user
            )
        
        # Refresh to get updated values
        inventory_item.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'new_stock': float(inventory_item.current_stock),
            'status': inventory_item.stock_status
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def lost_found_list(request):
    """List lost and found items for the current user's accessible properties."""
    
    # Get accessible properties using centralized authorization
    if request.user.is_superuser:
        properties = Property.objects.all()
    else:
        try:
            profile = request.user.profile
            user_role = profile.role
            
            if user_role == 'manager':
                # Managers can see all properties
                properties = Property.objects.all()
            else:
                # For regular staff, show items from properties where they have tasks
                # OR items they found themselves
                property_ids = Task.objects.filter(
                    assigned_to=request.user
                ).values_list('property_ref', flat=True).distinct()
                properties = Property.objects.filter(id__in=property_ids)
        except:
            # If no profile, only show properties with assigned tasks
            property_ids = Task.objects.filter(
                assigned_to=request.user
            ).values_list('property_ref', flat=True).distinct()
            properties = Property.objects.filter(id__in=property_ids)
    
    # Get lost & found items - show items from accessible properties OR items found by this user
    items = LostFoundItem.objects.filter(
        Q(property_ref__in=properties) | Q(found_by=request.user)
    ).select_related('property_ref', 'found_by').order_by('-found_date')
    
    logger.info(f"Lost & found list accessed by user: {request.user.username}")
    logger.info(f"Found {items.count()} items for user {request.user.username}")
    logger.info(f"Properties accessible: {[p.name for p in properties]}")
    logger.info(f"Items found: {[f'{item.title} - {item.property_ref.name}' for item in items[:5]]}")
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        items = items.filter(status=status_filter)
    
    context = {
        'items': items,
        'status_filter': status_filter,
        'status_choices': LostFoundItem.STATUS_CHOICES,
        'user': request.user,  # Add user to context
    }
    
    return render(request, 'staff/lost_found_list.html', context)


@login_required
@require_POST
def upload_checklist_photo(request):
    """Upload a photo for a checklist response."""
    
    try:
        item_id = request.POST.get('item_id')
        photo = request.FILES.get('photo')
        
        if not item_id or not photo:
            return JsonResponse({'error': 'Missing item_id or photo'}, status=400)
        
        response = get_object_or_404(ChecklistResponse, id=item_id)
        
        # Check permissions using centralized authorization
        if not can_edit_task(request.user, response.checklist.task):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Validate file type and size
        try:
            from api.models import validate_task_image
            validate_task_image(photo)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Check file size using consistent settings
        from django.conf import settings
        max_bytes = getattr(settings, 'MAX_UPLOAD_BYTES', 25 * 1024 * 1024)
        if photo.size > max_bytes:
            max_mb = max_bytes // (1024 * 1024)
            return JsonResponse({'error': f'File too large. Maximum size is {max_mb}MB.'}, status=400)
        
        # Unified path: create TaskImage associated to the task and link to ChecklistResponse
        task = response.checklist.task
        
        with transaction.atomic():
            # Lock existing rows for this task/type to compute next sequence safely
            existing_qs = (TaskImage.objects
                           .select_for_update()
                           .filter(task=task, photo_type='checklist'))
            next_seq = existing_qs.count() + 1
            task_image = TaskImage.objects.create(
                task=task,
                image=photo,
                uploaded_by=request.user,
                photo_type='checklist',
                sequence_number=next_seq,
                checklist_response=response,
            )
        
        return JsonResponse({
            'success': True,
            'photo_id': task_image.id,
            'photo_url': task_image.image.url
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def remove_checklist_photo(request):
    """Remove a photo from a checklist item."""

    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        photo_url = data.get('photo_url')

        if not item_id or not photo_url:
            return JsonResponse({'error': 'Missing item_id or photo_url'}, status=400)

        response = get_object_or_404(ChecklistResponse, id=item_id)

        # Check permissions
        if not can_edit_task(request.user, response.checklist.task):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        # Prefer deleting unified TaskImage; fall back to ChecklistPhoto for legacy
        filename = photo_url.split('/')[-1]
        # 1) Try TaskImage linked to this response and task
        task = response.checklist.task
        ti = TaskImage.objects.filter(task=task, checklist_response=response, image__endswith=filename).first()
        if ti:
            ti.image.delete(save=False)
            ti.delete()
            return JsonResponse({'success': True})
        
        # 2) Legacy: try ChecklistPhoto
        try:
            photo = ChecklistPhoto.objects.get(
                response=response,
                image__endswith=filename
            )
            photo.image.delete(save=False)
            photo.delete()
            return JsonResponse({'success': True})
        except ChecklistPhoto.DoesNotExist:
            logger.warning(f"ChecklistPhoto/TaskImage not found for response {item_id} with photo_url {photo_url}")
            return JsonResponse({'error': 'Photo not found'}, status=404)

    except Exception as e:
        logger.error(f"Error removing checklist photo: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def update_task_status_api(request, task_id):
    """Update task status via AJAX."""

    try:
        task = get_object_or_404(Task, id=task_id)

        # Check permissions
        if not can_edit_task(request.user, task):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        data = json.loads(request.body)
        new_status = data.get('status')
        new_description = data.get('description')

        if new_status and new_status not in [choice[0] for choice in Task.STATUS_CHOICES]:
            return JsonResponse({'error': 'Invalid status'}, status=400)

        old_status = task.status
        if new_status:
            task.status = new_status
        if new_description is not None:
            task.description = new_description
        task.modified_by = request.user
        task.save()

        logger.info(f"Task {task_id} status updated: {old_status} -> {new_status} by {request.user.username}")

        return JsonResponse({
            'success': True,
            'status': task.status,
            'status_display': task.get_status_display()
        })

    except Exception as e:
        logger.error(f"Error updating task {task_id} status: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def task_progress_api(request, task_id):
    """Get task progress information."""

    try:
        task = get_object_or_404(Task, id=task_id)

        # Check permissions
        if not can_view_task(request.user, task):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        # Get checklist progress
        try:
            checklist = task.checklist
            total_items = checklist.responses.count()
            completed_items = checklist.responses.filter(is_completed=True).count()
            percentage = int((completed_items / total_items) * 100) if total_items > 0 else 0
        except:
            total_items = 0
            completed_items = 0
            percentage = 0

        # Return flat fields and a nested object for backward compatibility
        return JsonResponse({
            'success': True,
            'completed': completed_items,
            'total': total_items,
            'percentage': percentage,
            'remaining': total_items - completed_items,
            'progress': {
                'completed': completed_items,
                'total': total_items,
                'percentage': percentage,
                'remaining': total_items - completed_items,
            }
        })

    except Exception as e:
        logger.error(f"Error getting task {task_id} progress: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def task_counts_api(request):
    """API endpoint for real-time task counts."""
    logger.info(f"Task counts API accessed by user: {request.user.username}")
    
    try:
        # Scope like staff_dashboard: managers/superusers/team-view see all tasks; others only assigned
        try:
            profile = request.user.profile
            is_manager = getattr(profile, 'role', '') == 'manager'
            can_view_team = bool(getattr(profile, 'can_view_team_tasks', False))
        except Profile.DoesNotExist:
            is_manager = False
            can_view_team = False

        if request.user.is_superuser or is_manager or can_view_team:
            scoped_tasks = Task.objects.all()
        else:
            scoped_tasks = Task.objects.filter(assigned_to=request.user)

        total_tasks = scoped_tasks.count()
        
        task_counts = {
            'total': total_tasks,
            'pending': scoped_tasks.filter(status='pending').count(),
            'in-progress': scoped_tasks.filter(status='in-progress').count(),
            'completed': scoped_tasks.filter(status='completed').count(),
            'overdue': scoped_tasks.filter(
                status__in=['pending', 'in-progress'],
                due_date__lt=timezone.now()
            ).count()
        }
        
        logger.debug(f"Task counts for user {request.user.username}: {task_counts}")
        
        return JsonResponse({
            'success': True,
            'counts': task_counts
        })
    except Exception as e:
        logger.error(f"Error in task_counts_api for user {request.user.username}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
def lost_found_create(request):
    """Create a new lost & found item from task context."""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['title', 'description', 'found_location', 'property_ref']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Get the property
        try:
            property_obj = Property.objects.get(id=data['property_ref'])
        except Property.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Property not found'
            }, status=400)
        
        # Get the task if provided
        task_obj = None
        if data.get('task'):
            try:
                task_obj = Task.objects.get(id=data['task'])
            except Task.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Task not found'
                }, status=400)
        
        # Get the booking if provided
        booking_obj = None
        if data.get('booking'):
            try:
                booking_obj = Booking.objects.get(id=data['booking'])
            except Booking.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Booking not found'
                }, status=400)
        
        # Create the lost & found item
        lost_found_item = LostFoundItem.objects.create(
            property_ref=property_obj,
            task=task_obj,
            booking=booking_obj,
            title=data['title'],
            description=data['description'],
            category=data.get('category', ''),
            estimated_value=data.get('estimated_value'),
            found_location=data['found_location'],
            storage_location=data.get('storage_location', ''),
            notes=data.get('notes', ''),
            found_by=request.user,
            status='found'
        )
        
        logger.info(f"Lost & found item created: {lost_found_item.title} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'item_id': lost_found_item.id,
            'message': 'Lost & found item reported successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error creating lost & found item: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
