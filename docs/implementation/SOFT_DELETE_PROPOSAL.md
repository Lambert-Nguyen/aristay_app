# 🗑️ Soft Delete Implementation Proposal

## Problem
Currently, all models use hard deletes, meaning:
- Deleted bookings/tasks/properties are permanently lost
- No audit trail of deleted items
- No ability to restore accidentally deleted data
- Compliance issues for audit requirements

## Proposed Solution: Soft Delete System

### 1. Add Soft Delete Fields to Models

```python
# Add to all major models (Booking, Property, Task, etc.)
class SoftDeleteMixin(models.Model):
    """Mixin to add soft delete functionality"""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='%(class)s_deleted'
    )
    deletion_reason = models.CharField(max_length=200, blank=True)
    
    class Meta:
        abstract = True
    
    def soft_delete(self, user=None, reason=""):
        """Soft delete this object"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.deletion_reason = reason
        self.save()
    
    def restore(self, user=None):
        """Restore soft deleted object"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = ""
        self.save()

class SoftDeleteManager(models.Manager):
    """Manager that excludes soft deleted objects by default"""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def with_deleted(self):
        """Include soft deleted objects"""
        return super().get_queryset()
    
    def only_deleted(self):
        """Only soft deleted objects"""
        return super().get_queryset().filter(is_deleted=True)
```

### 2. Update Models
```python
class Booking(SoftDeleteMixin, models.Model):
    # ... existing fields ...
    
    objects = SoftDeleteManager()  # Default manager excludes deleted
    all_objects = models.Manager()  # Includes deleted objects

class Property(SoftDeleteMixin, models.Model):
    # ... existing fields ...
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()

class Task(SoftDeleteMixin, models.Model):
    # ... existing fields ...
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
```

### 3. Admin Interface Updates
```python
# Admin actions for soft delete management
def soft_delete_selected(modeladmin, request, queryset):
    """Soft delete selected objects"""
    count = queryset.count()
    for obj in queryset:
        obj.soft_delete(user=request.user, reason="Admin bulk delete")
    messages.success(request, f"Soft deleted {count} items")

def restore_selected(modeladmin, request, queryset):
    """Restore soft deleted objects"""
    count = queryset.filter(is_deleted=True).count()
    for obj in queryset.filter(is_deleted=True):
        obj.restore(user=request.user)
    messages.success(request, f"Restored {count} items")

class BookingAdmin(admin.ModelAdmin):
    list_display = ('property', 'guest_name', 'check_in_date', 'status', 'is_deleted')
    list_filter = ('status', 'is_deleted', 'deleted_at')
    actions = [soft_delete_selected, restore_selected]
    
    def get_queryset(self, request):
        # Show both active and deleted items in admin
        return self.model.all_objects.get_queryset()
```

### 4. API Updates
```python
# Update API views to handle soft delete
class BookingViewSet(viewsets.ModelViewSet):
    def destroy(self, request, *args, **kwargs):
        """Override delete to use soft delete"""
        instance = self.get_object()
        instance.soft_delete(user=request.user, reason="API delete")
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore a soft deleted booking"""
        booking = self.get_object()
        if booking.is_deleted:
            booking.restore(user=request.user)
            return Response({'status': 'restored'})
        return Response({'error': 'Booking is not deleted'}, 
                       status=status.HTTP_400_BAD_REQUEST)
```

### 5. Frontend Updates
```dart
// Add restore functionality to Flutter frontend
Future<void> _restoreBooking(int bookingId) async {
  try {
    await ApiService().restoreBooking(bookingId);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Booking restored successfully'))
    );
    _loadBookings(); // Refresh list
  } catch (e) {
    // Handle error
  }
}
```

### 6. Benefits
✅ **Data Recovery**: Restore accidentally deleted items
✅ **Audit Trail**: Complete history of what was deleted and when
✅ **Compliance**: Meet regulatory requirements for data retention
✅ **User Safety**: Reduces risk of permanent data loss
✅ **Reporting**: Generate reports on deleted items
✅ **Cascading Logic**: Handle related object deletions gracefully

### 7. Migration Strategy
1. **Phase 1**: Add soft delete fields to models (migration)
2. **Phase 2**: Update managers and querysets
3. **Phase 3**: Update admin interface with restore actions
4. **Phase 4**: Update API endpoints
5. **Phase 5**: Update frontend to show/restore deleted items
6. **Phase 6**: Add cleanup job for permanently deleting old soft-deleted items

### 8. Cascade Handling
```python
# When booking is soft deleted, soft delete related tasks
def soft_delete(self, user=None, reason=""):
    super().soft_delete(user, reason)
    
    # Soft delete related tasks
    for task in self.tasks.filter(is_deleted=False):
        task.soft_delete(user=user, reason=f"Booking deleted: {reason}")
```
