# Lost & Found Feature - Technical Implementation Guide

**Date:** September 9, 2025  
**Version:** 1.0  
**Audience:** Developers, Technical Reviewers  

## 🎯 Overview

This technical guide provides detailed implementation information for the Lost & Found feature in the Aristay Property Management System. It covers database schema, API endpoints, frontend implementation, and integration patterns.

## 🗄️ Database Schema

### LostFoundItem Model

```python
class LostFoundItem(models.Model):
    """Items found or reported lost at properties."""
    STATUS_CHOICES = [
        ('found', 'Found'),
        ('claimed', 'Claimed'),
        ('disposed', 'Disposed'),
        ('donated', 'Donated'),
    ]
    
    # Core relationships
    property_ref = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='lost_found_items')
    task = models.ForeignKey('Task', on_delete=models.SET_NULL, null=True, blank=True, help_text="Task during which item was found")
    booking = models.ForeignKey('Booking', on_delete=models.SET_NULL, null=True, blank=True, help_text="Associated booking if known")
    
    # Item details
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, blank=True, help_text="e.g., Electronics, Clothing, Jewelry")
    estimated_value = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Location & status
    found_location = models.CharField(max_length=200, help_text="Where in the property was it found")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='found')
    
    # Tracking
    found_date = models.DateTimeField(auto_now_add=True)
    found_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='found_items')
    claimed_date = models.DateTimeField(null=True, blank=True)
    claimed_by = models.CharField(max_length=200, blank=True, help_text="Name of person who claimed it")
    
    # Storage
    storage_location = models.CharField(max_length=200, blank=True, help_text="Where item is currently stored")
    disposal_date = models.DateTimeField(null=True, blank=True)
    disposal_method = models.CharField(max_length=100, blank=True)
    
    # Additional
    notes = models.TextField(blank=True)
    history = models.TextField(blank=True, help_text="JSON field tracking changes to this item")
    
    class Meta:
        ordering = ['-found_date']
    
    def __str__(self):
        return f"{self.title} - {self.property_ref.name} ({self.get_status_display()})"
```

### LostFoundPhoto Model

```python
class LostFoundPhoto(models.Model):
    """Photos of lost & found items."""
    item = models.ForeignKey(LostFoundItem, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='lost_found/%Y/%m/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
```

## 🔧 API Implementation

### Staff Portal Endpoints

#### Create Lost & Found Item
```python
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
```

#### List Lost & Found Items
```python
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
```

## 🎨 Frontend Implementation

### Task Detail Integration

#### HTML Modal Structure
```html
<!-- Lost & Found Modal -->
<div id="lostFoundModal" class="lost-found-modal" style="display: none;">
    <div class="modal-backdrop"></div>
    <div class="modal-content">
        <div class="modal-header">
            <h3>🔍 Report Lost & Found Item</h3>
            <button class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
            <form id="lostFoundForm" class="item-form">
                <div class="form-group">
                    <label class="form-label">Item Title *</label>
                    <input type="text" class="form-control" name="title" required placeholder="e.g., iPhone 12, Wedding Ring, etc.">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Description *</label>
                    <textarea class="form-control" name="description" rows="3" required placeholder="Describe the item in detail..."></textarea>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Category</label>
                        <select class="form-control" name="category">
                            <option value="">Select category...</option>
                            <option value="Electronics">Electronics</option>
                            <option value="Clothing">Clothing</option>
                            <option value="Jewelry">Jewelry</option>
                            <option value="Personal Items">Personal Items</option>
                            <option value="Documents">Documents</option>
                            <option value="Toys">Toys</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Estimated Value ($)</label>
                        <input type="number" class="form-control" name="estimated_value" step="0.01" min="0" placeholder="0.00">
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Found Location *</label>
                    <input type="text" class="form-control" name="found_location" required placeholder="e.g., Master bedroom, Kitchen counter, etc.">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Storage Location</label>
                    <input type="text" class="form-control" name="storage_location" placeholder="Where will this item be stored?">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Additional Notes</label>
                    <textarea class="form-control" name="notes" rows="2" placeholder="Any additional information..."></textarea>
                </div>
                
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary modal-close-btn">Cancel</button>
                    <button type="submit" class="btn btn-primary">Report Item</button>
                </div>
            </form>
        </div>
    </div>
</div>
```

#### JavaScript Implementation
```javascript
// Open modal function
window.reportLostFound = function() {
    console.log('🔍 Opening lost & found modal...');
    const modal = document.getElementById('lostFoundModal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Pre-fill some fields based on task context
        const foundLocationInput = modal.querySelector('input[name="found_location"]');
        if (foundLocationInput && !foundLocationInput.value) {
            foundLocationInput.value = '{{ task.property_ref.name }} - Task: {{ task.title }}';
        }
        
        // Ensure form is reset and event listeners are fresh
        const form = modal.querySelector('#lostFoundForm');
        if (form) {
            // Remove any existing event listeners by cloning the form
            const newForm = form.cloneNode(true);
            form.parentNode.replaceChild(newForm, form);
            
            // Re-add event listener
            newForm.addEventListener('submit', handleLostFoundSubmit);
            console.log('🔍 Lost & found form event listener attached');
        }
    } else {
        console.error('🔍 Lost & found modal not found!');
    }
};

// Form submission handler
async function handleLostFoundSubmit(e) {
    e.preventDefault();
    console.log('🔍 Submitting lost & found item...');
    
    const form = e.target;
    const formData = new FormData(form);
    
    // Validate required fields
    const title = formData.get('title').trim();
    const description = formData.get('description').trim();
    const foundLocation = formData.get('found_location').trim();
    
    if (!title || !description || !foundLocation) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }
    
    try {
        const taskId = {{ task.id }};
        const csrfToken = getCsrfToken();
        
        const lostFoundData = {
            title: title,
            description: description,
            category: formData.get('category') || '',
            estimated_value: formData.get('estimated_value') || null,
            found_location: foundLocation,
            storage_location: formData.get('storage_location') || '',
            notes: formData.get('notes') || '',
            property_ref: {{ task.property_ref.id }},
            task: taskId,
            {% if task.booking %}
            booking: {{ task.booking.id }},
            {% endif %}
            status: 'found'
        };
        
        const response = await fetch('/api/staff/lost-found/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(lostFoundData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification('Lost & found item reported successfully!', 'success');
            closeModal();
            
            // Reset form
            form.reset();
            
            // Optionally redirect to lost & found list
            setTimeout(() => {
                window.location.href = '/api/staff/lost-found/';
            }, 1500);
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to report item');
        }
    } catch (error) {
        console.error('Error reporting lost & found item:', error);
        showNotification('Failed to report item: ' + error.message, 'error');
    }
}
```

### CSS Styling
```css
/* Lost & Found Button */
.btn-action.report-lost-found {
    background: rgba(168, 85, 247, 0.8);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-action.report-lost-found:hover {
    background: rgba(168, 85, 247, 1);
    transform: translateY(-1px);
}

/* Modal Styling */
.lost-found-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1000;
}

.lost-found-modal .modal-backdrop {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
}

.lost-found-modal .modal-content {
    position: relative;
    background: white;
    margin: 2rem auto;
    max-width: 600px;
    border-radius: 0.5rem;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    max-height: 90vh;
    overflow-y: auto;
}

/* Form Layout */
.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}

@media (max-width: 640px) {
    .form-row {
        grid-template-columns: 1fr;
    }
}
```

## 📊 History Tracking Implementation

### Detailed Change Logging
```python
def save(self, *args, **kwargs):
    # Only build history on updates, not on initial creation
    if self.pk:
        try:
            old = LostFoundItem.objects.get(pk=self.pk)
            changes = []
            
            # Get the current user making the change
            user = self._get_current_user()
            
            # Title change
            if old.title != self.title:
                changes.append(
                    f"{timezone.now().isoformat()}: {user} changed title "
                    f"from '{old.title}' to '{self.title}'"
                )
            
            # Description change
            if old.description != self.description:
                changes.append(
                    f"{timezone.now().isoformat()}: {user} changed description "
                    f"from '{old.description}' to '{self.description}'"
                )
            
            # Status change
            if old.status != self.status:
                changes.append(
                    f"{timezone.now().isoformat()}: {user} changed status "
                    f"from '{old.get_status_display()}' to '{self.get_status_display()}'"
                )
            
            # ... similar for all other fields
            
            # Update history if there are changes
            if changes:
                import json
                hist = json.loads(old.history or "[]")
                self.history = json.dumps(hist + changes)
                
        except LostFoundItem.DoesNotExist:
            pass  # This is a new item, no history to build
    
    super().save(*args, **kwargs)

def _get_current_user(self):
    """Get the current user making the change."""
    user = 'system'  # Default fallback
    
    # Try to get the current user from thread-local storage (Django admin sets this)
    try:
        from django.contrib.auth import get_user
        current_user = get_user()
        if current_user and not current_user.is_anonymous:
            user = current_user.username
        else:
            # Fallback: try to get from the most recent LogEntry
            from django.contrib.admin.models import LogEntry
            from django.contrib.contenttypes.models import ContentType
            
            content_type = ContentType.objects.get_for_model(self)
            recent_log = LogEntry.objects.filter(
                object_id=str(self.pk),
                content_type=content_type
            ).order_by('-action_time').first()
            
            if recent_log:
                user = recent_log.user.username
            else:
                # Final fallback to found_by
                user = getattr(self.found_by, 'username', 'system') if self.found_by else 'system'
    except:
        # If we can't get the current user, use found_by as fallback
        user = getattr(self.found_by, 'username', 'system') if self.found_by else 'system'
    
    return user
```

## 🔧 Django Admin Integration

### Admin Configuration
```python
class LostFoundItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'property_ref', 'status', 'found_date', 'found_by', 'estimated_value')
    list_filter = ('status', 'found_date', 'property_ref', 'category')
    search_fields = ('title', 'description', 'property_ref__name', 'found_location')
    readonly_fields = ('found_date', 'history')
    inlines = [LostFoundPhotoInline]
    
    # Use the generic unified history view
    history_view = create_unified_history_view(LostFoundItem)
    
    def get_readonly_fields(self, request, obj=None):
        """Make history field read-only in the admin form"""
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if 'history' not in readonly_fields:
            readonly_fields.append('history')
        return readonly_fields
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'category', 'estimated_value', 'property_ref', 'task', 'booking')
        }),
        ('Location & Status', {
            'fields': ('found_location', 'status', 'storage_location')
        }),
        ('Found Info', {
            'fields': ('found_date', 'found_by'),
            'classes': ('collapse',)
        }),
        ('Claimed Info', {
            'fields': ('claimed_date', 'claimed_by'),
            'classes': ('collapse',)
        }),
        ('Disposal Info', {
            'fields': ('disposal_date', 'disposal_method'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('History', {
            'fields': ('history',),
            'classes': ('collapse',)
        }),
    )
```

## 🧪 Testing Implementation

### Unit Tests
```python
@pytest.mark.django_db
def test_lost_found_item_creation():
    """Test creating a lost & found item."""
    user = User.objects.create_user(username='testuser', password='testpass')
    property_obj = Property.objects.create(name='Test Property', address='123 Test St')
    
    item = LostFoundItem.objects.create(
        title='Test Item',
        description='Test description',
        found_location='Test location',
        property_ref=property_obj,
        found_by=user
    )
    
    assert item.title == 'Test Item'
    assert item.status == 'found'
    assert item.found_by == user

@pytest.mark.django_db
def test_lost_found_history_tracking():
    """Test history tracking for lost & found items."""
    user = User.objects.create_user(username='testuser', password='testpass')
    property_obj = Property.objects.create(name='Test Property', address='123 Test St')
    
    item = LostFoundItem.objects.create(
        title='Test Item',
        description='Test description',
        found_location='Test location',
        property_ref=property_obj,
        found_by=user
    )
    
    # Update the item
    item.title = 'Updated Item'
    item.save()
    
    # Check history
    import json
    history = json.loads(item.history or "[]")
    assert len(history) == 1
    assert 'changed title' in history[0]
    assert 'Test Item' in history[0]
    assert 'Updated Item' in history[0]
```

### Integration Tests
```python
@pytest.mark.django_db
def test_lost_found_api_creation():
    """Test API endpoint for creating lost & found items."""
    user = User.objects.create_user(username='testuser', password='testpass')
    property_obj = Property.objects.create(name='Test Property', address='123 Test St')
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    data = {
        'title': 'Test Item',
        'description': 'Test description',
        'found_location': 'Test location',
        'property_ref': property_obj.id,
        'status': 'found'
    }
    
    response = client.post('/api/staff/lost-found/create/', data, format='json')
    assert response.status_code == 200
    
    result = response.json()
    assert result['success'] is True
    assert 'item_id' in result
```

## 🚀 Deployment Checklist

### Database Migrations
- [ ] Run migration `0061_add_lost_found_history.py`
- [ ] Verify history field is added to LostFoundItem table
- [ ] Test data integrity

### File Storage
- [ ] Configure media root for image uploads
- [ ] Set up proper file permissions
- [ ] Test image upload functionality

### Admin Configuration
- [ ] Register LostFoundItemAdmin
- [ ] Test admin interface functionality
- [ ] Verify history view works correctly

### API Endpoints
- [ ] Test all API endpoints
- [ ] Verify authentication and authorization
- [ ] Test error handling

### Frontend Integration
- [ ] Test modal functionality
- [ ] Verify form validation
- [ ] Test responsive design
- [ ] Cross-browser compatibility

## 🔍 Troubleshooting

### Common Issues

#### History Not Tracking
- Check if `_get_current_user()` method is working correctly
- Verify Django admin is setting thread-local user
- Check LogEntry fallback mechanism

#### Modal Not Opening
- Verify JavaScript event listeners are attached
- Check for console errors
- Ensure modal HTML is present in DOM

#### API Errors
- Check CSRF token handling
- Verify authentication requirements
- Check data validation

#### File Upload Issues
- Verify media root configuration
- Check file permissions
- Test image validation

### Debug Commands
```python
# Check history tracking
item = LostFoundItem.objects.get(id=1)
print(item.history)

# Check user attribution
from django.contrib.auth import get_user
user = get_user()
print(f"Current user: {user}")

# Check LogEntry
from django.contrib.admin.models import LogEntry
logs = LogEntry.objects.filter(object_id='1')
for log in logs:
    print(f"{log.action_time}: {log.user} - {log.change_message}")
```

---

**Document Version:** 1.0  
**Last Updated:** September 9, 2025  
**Next Review:** December 9, 2025  
**Maintained By:** Development Team
