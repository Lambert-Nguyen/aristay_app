"""
Staff Portal Views - Role-based interfaces for different staff types.
Provides specialized dashboards and workflows for each user role.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count, Prefetch, F
from django.core.paginator import Paginator
import json
import logging

# Set up logging
logger = logging.getLogger(__name__)

from .models import (
    Task, Property, TaskChecklist, ChecklistResponse, ChecklistPhoto,
    PropertyInventory, InventoryTransaction, LostFoundItem, Profile,
    TASK_TYPE_CHOICES
)
from .serializers import TaskSerializer


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
    
    # Get user's task summary
    my_tasks = Task.objects.filter(assigned_to=request.user)
    total_tasks = my_tasks.count()
    
    task_counts = {
        'pending': my_tasks.filter(status='pending').count(),
        'in_progress': my_tasks.filter(status='in-progress').count(),
        'completed': my_tasks.filter(status='completed').count(),
        'overdue': my_tasks.filter(
            status__in=['pending', 'in-progress'],
            due_date__lt=timezone.now()
        ).count()
    }
    
    logger.debug(f"User {request.user.username} has {total_tasks} total tasks: {task_counts}")
    
    # Get recent tasks
    recent_tasks = my_tasks.select_related('property', 'booking').order_by('-created_at')[:5]
    
    # Get properties user has access to
    accessible_properties = Property.objects.all()[:5]
    
    context = {
        'user_role': user_role,
        'total_tasks': total_tasks,
        'task_counts': task_counts,
        'recent_tasks': recent_tasks,
        'accessible_properties': accessible_properties,
    }
    
    logger.info(f"Staff dashboard rendered successfully for user: {request.user.username}")
    return render(request, 'staff/dashboard.html', context)


@login_required
def cleaning_dashboard(request):
    """Specialized dashboard for cleaning staff."""
    
    # Get user's assigned cleaning tasks
    assigned_tasks = Task.objects.filter(
        assigned_to=request.user,
        task_type='cleaning',
        status__in=['pending', 'in_progress']
    ).select_related('property', 'booking').prefetch_related('checklist__responses')
    
    # Get today's tasks
    today = timezone.now().date()
    today_tasks = assigned_tasks.filter(due_date__date=today)
    
    # Get upcoming tasks (next 7 days)
    upcoming_tasks = assigned_tasks.filter(
        due_date__date__gt=today,
        due_date__date__lte=today + timezone.timedelta(days=7)
    )
    
    # Get checklist progress
    tasks_with_progress = []
    for task in assigned_tasks:
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
        'today_tasks': today_tasks,
        'upcoming_tasks': upcoming_tasks,
        'tasks_with_progress': tasks_with_progress,
        'total_assigned': assigned_tasks.count(),
    }
    
    return render(request, 'staff/cleaning_dashboard.html', context)


@login_required
def maintenance_dashboard(request):
    """Specialized dashboard for maintenance staff."""
    
    # Get user's assigned maintenance tasks
    assigned_tasks = Task.objects.filter(
        assigned_to=request.user,
        task_type='maintenance',
        status__in=['pending', 'in_progress']
    ).select_related('property', 'booking')
    
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
    overdue_tasks = assigned_tasks.filter(due_date__lt=now)
    today_tasks = assigned_tasks.filter(due_date__date=today)
    
    context = {
        'user_role': 'Maintenance Staff',
        'assigned_tasks': assigned_tasks,
        'overdue_tasks': overdue_tasks,
        'today_tasks': today_tasks,
        'low_stock_items': low_stock_items,
        'recent_transactions': recent_transactions,
        'total_assigned': assigned_tasks.count(),
    }
    
    return render(request, 'staff/maintenance_dashboard.html', context)


@login_required
def laundry_dashboard(request):
    """Specialized dashboard for laundry staff."""
    
    # Get user's assigned laundry tasks
    assigned_tasks = Task.objects.filter(
        assigned_to=request.user,
        task_type='laundry',
        status__in=['pending', 'in_progress']
    ).select_related('property', 'booking')
    
    # Organize by workflow stage based on task status/progress
    pickup_tasks = assigned_tasks.filter(status='pending')
    processing_tasks = assigned_tasks.filter(status='in_progress')
    
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
        'total_assigned': assigned_tasks.count(),
    }
    
    return render(request, 'staff/laundry_dashboard.html', context)


@login_required
def lawn_pool_dashboard(request):
    """Specialized dashboard for lawn/pool staff."""
    
    # Get user's assigned lawn/pool tasks
    assigned_tasks = Task.objects.filter(
        assigned_to=request.user,
        task_type='lawn_pool',
        status__in=['pending', 'in_progress']
    ).select_related('property', 'booking')
    
    # Get pool/spa inventory items
    pool_items = PropertyInventory.objects.filter(
        item__category__name='Pool & Spa'
    ).select_related('property_ref', 'item')
    
    # Group tasks by property for route planning
    tasks_by_property = {}
    for task in assigned_tasks:
        prop_name = task.property.name if task.property else 'Unassigned'
        if prop_name not in tasks_by_property:
            tasks_by_property[prop_name] = []
        tasks_by_property[prop_name].append(task)
    
    context = {
        'user_role': 'Lawn/Pool Staff',
        'assigned_tasks': assigned_tasks,
        'tasks_by_property': tasks_by_property,
        'pool_items': pool_items,
        'total_assigned': assigned_tasks.count(),
    }
    
    return render(request, 'staff/lawn_pool_dashboard.html', context)


@login_required
def task_detail(request, task_id):
    """Detailed task view with checklist interface."""
    
    task = get_object_or_404(
        Task.objects.select_related('property', 'booking', 'assigned_to'),
        id=task_id
    )
    
    # Check if user can access this task
    if not (request.user.is_staff or task.assigned_to == request.user):
        messages.error(request, "You don't have permission to view this task.")
        return redirect('/api/staff/')
    
    # Get or create checklist
    try:
        checklist = task.checklist
        responses = checklist.responses.select_related('item').prefetch_related('photos')
    except:
        checklist = None
        responses = []
    
    # Group responses by room type for better organization
    responses_by_room = {}
    for response in responses:
        room = response.item.room_type or 'General'
        if room not in responses_by_room:
            responses_by_room[room] = []
        responses_by_room[room].append(response)
    
    context = {
        'task': task,
        'checklist': checklist,
        'responses_by_room': responses_by_room,
        'can_edit': task.assigned_to == request.user or request.user.is_staff,
    }
    
    return render(request, 'staff/task_detail.html', context)


@login_required
@require_POST
def update_checklist_response(request, response_id):
    """Update a checklist response via AJAX."""
    
    response = get_object_or_404(ChecklistResponse, id=response_id)
    
    # Check permissions
    if not (request.user.is_staff or response.checklist.task.assigned_to == request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
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
def my_tasks(request):
    """List of all tasks assigned to current user."""
    
    tasks = Task.objects.filter(
        assigned_to=request.user
    ).select_related('property', 'booking').order_by('-due_date')
    
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
            Q(property__name__icontains=search)
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
    }
    
    return render(request, 'staff/my_tasks.html', context)


@login_required
def inventory_lookup(request):
    """Inventory lookup interface for maintenance staff."""
    
    # Check if user should have inventory access
    # Superusers, managers, and maintenance department staff have access
    if not request.user.is_superuser:
        try:
            profile = request.user.profile
            user_role = profile.role
            
            # Allow managers and users in Maintenance department
            if user_role != 'manager' and not profile.is_in_department('Maintenance'):
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
    }
    
    return render(request, 'staff/inventory_lookup.html', context)


@login_required
@require_POST
def log_inventory_transaction(request):
    """Log an inventory transaction."""
    
    try:
        data = json.loads(request.body)
        
        inventory_item = get_object_or_404(
            PropertyInventory,
            id=data['inventory_id']
        )
        
        # Create transaction
        transaction = InventoryTransaction.objects.create(
            property_inventory=inventory_item,
            transaction_type=data['transaction_type'],
            quantity=float(data['quantity']),
            notes=data.get('notes', ''),
            task_id=data.get('task_id'),
            created_by=request.user
        )
        
        # Update inventory levels
        if data['transaction_type'] in ['stock_in', 'adjustment']:
            inventory_item.current_stock += float(data['quantity'])
        elif data['transaction_type'] in ['stock_out', 'damage']:
            inventory_item.current_stock -= float(data['quantity'])
        
        inventory_item.updated_by = request.user
        inventory_item.save()
        
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
    
    # Get accessible properties
    if request.user.is_staff:
        properties = Property.objects.all()
    else:
        # For regular staff, show items from properties where they have tasks
        property_ids = Task.objects.filter(
            assigned_to=request.user
        ).values_list('property', flat=True).distinct()
        properties = Property.objects.filter(id__in=property_ids)
    
    # Get lost & found items
    items = LostFoundItem.objects.filter(
        property_ref__in=properties
    ).select_related('property_ref', 'found_by').order_by('-found_date')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        items = items.filter(status=status_filter)
    
    context = {
        'items': items,
        'status_filter': status_filter,
        'status_choices': LostFoundItem.STATUS_CHOICES,
    }
    
    return render(request, 'staff/lost_found_list.html', context)


@login_required
@require_POST
def upload_checklist_photo(request):
    """Upload a photo for a checklist response."""
    
    try:
        response_id = request.POST.get('response_id')
        photo = request.FILES.get('photo')
        
        if not response_id or not photo:
            return JsonResponse({'error': 'Missing response_id or photo'}, status=400)
        
        response = get_object_or_404(ChecklistResponse, id=response_id)
        
        # Check permissions
        if not (request.user.is_staff or response.checklist.task.assigned_to == request.user):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Create photo record
        checklist_photo = ChecklistPhoto.objects.create(
            response=response,
            image=photo,
            uploaded_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'photo_id': checklist_photo.id,
            'photo_url': checklist_photo.image.url
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def set_task_status(request, task_id):
    """Update a task's status."""
    
    logger.info(f"Task status update requested by user {request.user.username} for task {task_id}")
    
    try:
        task = get_object_or_404(Task, id=task_id)
        old_status = task.status
        
        # Check permissions
        if not (request.user.is_staff or task.assigned_to == request.user):
            logger.warning(f"Permission denied for user {request.user.username} to update task {task_id}")
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        data = json.loads(request.body)
        new_status = data.get('status')
        
        logger.debug(f"Task {task_id} status change requested: {old_status} -> {new_status}")
        
        if new_status not in [choice[0] for choice in Task.STATUS_CHOICES]:
            logger.warning(f"Invalid status '{new_status}' requested for task {task_id}")
            return JsonResponse({'error': 'Invalid status'}, status=400)
        
        task.status = new_status
        task.modified_by = request.user
        task.save()
        
        logger.info(f"Task {task_id} status updated successfully: {old_status} -> {new_status} by user {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'status': task.status,
            'status_display': task.get_status_display()
        })
        
    except Exception as e:
        logger.error(f"Error updating task {task_id} status by user {request.user.username}: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def task_counts_api(request):
    """API endpoint for real-time task counts."""
    logger.info(f"Task counts API accessed by user: {request.user.username}")
    
    try:
        # Get user's task summary
        my_tasks = Task.objects.filter(assigned_to=request.user)
        total_tasks = my_tasks.count()
        
        task_counts = {
            'total': total_tasks,
            'pending': my_tasks.filter(status='pending').count(),
            'in_progress': my_tasks.filter(status='in-progress').count(),
            'completed': my_tasks.filter(status='completed').count(),
            'overdue': my_tasks.filter(
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
