# 📸 Before/After Photo System - September 10, 2025

## 🎯 **Overview**

The Before/After Photo System enhances the TaskImage model to support comprehensive photo categorization, approval workflows, and before/after comparison functionality for property management tasks.

## ✨ **Key Features**

### **1. Photo Type Categorization**
- **Before Photos**: Initial state documentation
- **After Photos**: Completed work documentation  
- **During Photos**: Work-in-progress documentation
- **Reference Photos**: General reference images
- **Damage Photos**: Damage documentation
- **General Photos**: Miscellaneous images

### **2. Approval Workflow**
- **Pending Review**: Newly uploaded photos awaiting approval
- **Approved**: Photos approved by management
- **Rejected**: Photos that don't meet standards
- **Archived**: Photos moved to archive

### **3. Photo Management**
- **Primary Photo Designation**: One primary photo per type per task
- **Sequence Numbering**: Ordered photos within each type
- **Detailed Descriptions**: Rich descriptions for each photo
- **Automatic Primary Assignment**: First photo of each type becomes primary

## 🏗️ **Technical Implementation**

### **Enhanced TaskImage Model**

```python
class TaskImage(models.Model):
    # Photo type choices for before/after functionality
    PHOTO_TYPE_CHOICES = [
        ('before', 'Before'),
        ('after', 'After'),
        ('during', 'During'),
        ('reference', 'Reference'),
        ('damage', 'Damage'),
        ('general', 'General'),
    ]
    
    # Photo status choices for approval workflow
    PHOTO_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]
    
    # Core fields
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=task_image_upload_path, validators=[validate_task_image])
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # NEW: Before/After photo categorization
    photo_type = models.CharField(
        max_length=20,
        choices=PHOTO_TYPE_CHOICES,
        default='general',
        help_text="Type of photo for before/after comparison"
    )
    
    # NEW: Photo status for approval workflow
    photo_status = models.CharField(
        max_length=20,
        choices=PHOTO_STATUS_CHOICES,
        default='pending',
        help_text="Approval status of the photo"
    )
    
    # NEW: Photo grouping and ordering
    sequence_number = models.PositiveIntegerField(
        default=1,
        help_text="Order within the same photo_type group"
    )
    
    # NEW: Primary photo designation
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary photo for this type (e.g., main 'before' photo)"
    )
    
    # NEW: Detailed description
    description = models.TextField(
        blank=True,
        help_text="Detailed description of what the photo shows"
    )
```

### **Database Constraints**

```python
class Meta:
    ordering = ['task', 'photo_type', 'sequence_number', 'uploaded_at']
    unique_together = ['task', 'photo_type', 'sequence_number']
    indexes = [
        models.Index(fields=['task', 'photo_type']),
        models.Index(fields=['photo_status']),
        models.Index(fields=['uploaded_at']),
    ]
```

### **Enhanced Serializer**

```python
class TaskImageSerializer(serializers.ModelSerializer):
    photo_type_display = serializers.CharField(source='get_photo_type_display', read_only=True)
    photo_status_display = serializers.CharField(source='get_photo_status_display', read_only=True)
    
    class Meta:
        model = TaskImage
        fields = [
            'id', 'task', 'image', 'uploaded_at', 'uploaded_by', 'uploaded_by_username',
            'size_bytes', 'width', 'height', 'original_size_bytes',
            # NEW: Before/After photo fields
            'photo_type', 'photo_type_display', 'photo_status', 'photo_status_display',
            'sequence_number', 'is_primary', 'description'
        ]
```

## 🔄 **Data Flow & Relationships**

### **Model Relationships**
```
Property (1) ──→ (many) Booking
    │
    └─── (many) Task ──→ (many) TaskImage
```

### **Photo Organization**
- **Property** → **Booking** → **Task** → **TaskImage** (with photo_type)
- Each task can have multiple photos of different types
- Each photo type can have multiple photos with sequence numbers
- One primary photo per type per task

## 📊 **Query Patterns**

### **Get Before/After Photo Pairs**
```python
# Get before photos for a task
before_photos = TaskImage.objects.filter(
    task=task,
    photo_type='before'
).order_by('sequence_number')

# Get after photos for a task
after_photos = TaskImage.objects.filter(
    task=task,
    photo_type='after'
).order_by('sequence_number')
```

### **Get Primary Photos**
```python
# Get all primary photos for a task
primary_photos = TaskImage.objects.filter(
    task=task,
    is_primary=True
)

# Get primary before photo
primary_before = TaskImage.objects.filter(
    task=task,
    photo_type='before',
    is_primary=True
).first()
```

### **Get Photos by Status**
```python
# Get approved photos
approved_photos = TaskImage.objects.filter(
    photo_status='approved'
)

# Get pending photos for review
pending_photos = TaskImage.objects.filter(
    photo_status='pending'
)
```

### **Get Photos for Booking**
```python
# Get all photos for a booking
booking_photos = TaskImage.objects.filter(
    task__booking=booking
)

# Get before photos for a booking
before_photos = TaskImage.objects.filter(
    task__booking=booking,
    photo_type='before'
)
```

## 🧪 **Testing**

### **Test Coverage**
- ✅ Model field validation
- ✅ Photo type and status choices
- ✅ Auto-primary photo assignment
- ✅ String representation
- ✅ Photo workflow states
- ✅ Query patterns by type, status, and booking
- ✅ Serializer field inclusion
- ✅ Database constraints

### **Test Files**
- `tests/unit/test_before_after_photos_final.py` - Core functionality tests
- `tests/unit/test_before_after_photos_simple.py` - Extended tests
- `tests/unit/test_before_after_photos.py` - Full integration tests

### **Running Tests**
```bash
# Run core functionality tests
python -m pytest tests/unit/test_before_after_photos_final.py -v

# Run all photo tests
python -m pytest tests/unit/test_before_after_photos*.py -v
```

## 🚀 **Usage Examples**

### **Creating Before/After Photos**

```python
# Create a before photo
before_photo = TaskImage.objects.create(
    task=cleaning_task,
    image=before_image_file,
    uploaded_by=staff_user,
    photo_type='before',
    description='Property before cleaning',
    sequence_number=1
)

# Create an after photo
after_photo = TaskImage.objects.create(
    task=cleaning_task,
    image=after_image_file,
    uploaded_by=staff_user,
    photo_type='after',
    description='Property after cleaning',
    sequence_number=1
)
```

### **API Usage**

```python
# Upload before photo via API
data = {
    'task': task_id,
    'image': image_file,
    'photo_type': 'before',
    'description': 'Initial state',
    'sequence_number': 1
}
response = client.post('/api/task-images/', data, format='multipart')

# Update photo status
data = {'photo_status': 'approved'}
response = client.patch(f'/api/task-images/{photo_id}/', data)
```

### **Querying Photos**

```python
# Get all photos for a task organized by type
photos_by_type = {}
for photo_type, _ in TaskImage.PHOTO_TYPE_CHOICES:
    photos_by_type[photo_type] = TaskImage.objects.filter(
        task=task,
        photo_type=photo_type
    ).order_by('sequence_number')

# Get before/after comparison data
before_after_data = {
    'before': TaskImage.objects.filter(task=task, photo_type='before'),
    'after': TaskImage.objects.filter(task=task, photo_type='after')
}
```

## 🔧 **Migration Details**

### **Migration File**
- `api/migrations/0068_add_before_after_photo_fields_only.py`

### **Changes Applied**
- Added `photo_type` field with choices
- Added `photo_status` field with choices  
- Added `sequence_number` field for ordering
- Added `is_primary` field for primary designation
- Added `description` field for detailed descriptions
- Updated model ordering and constraints
- Added database indexes for performance

## 📈 **Benefits**

### **For Property Managers**
- **Visual Documentation**: Clear before/after comparisons
- **Quality Control**: Approval workflow ensures standards
- **Progress Tracking**: During photos show work progress
- **Damage Documentation**: Dedicated damage photo category

### **For Staff**
- **Clear Instructions**: Photo types guide what to capture
- **Easy Organization**: Sequence numbers maintain order
- **Flexible Workflow**: Multiple photos per type supported

### **For System**
- **Data Integrity**: Constraints prevent invalid states
- **Performance**: Indexed queries for fast retrieval
- **Scalability**: Efficient query patterns for large datasets

## 🔮 **Future Enhancements**

### **Potential Features**
- **Photo Comparison UI**: Side-by-side before/after display
- **Bulk Photo Operations**: Mass approval/rejection
- **Photo Annotations**: Drawing tools for photo markup
- **Automated Quality Checks**: AI-powered photo validation
- **Photo Templates**: Predefined photo sets for common tasks

### **Integration Opportunities**
- **Mobile App**: Enhanced photo capture with type selection
- **Reporting**: Before/after photo reports
- **Client Portal**: Photo sharing with property owners
- **Analytics**: Photo usage and approval metrics

## 📋 **Implementation Checklist**

- ✅ Enhanced TaskImage model with new fields
- ✅ Database migration applied
- ✅ Updated TaskImageSerializer
- ✅ Added model validation and constraints
- ✅ Created comprehensive test suite
- ✅ Documented API usage patterns
- ✅ Established query patterns
- ✅ Validated data integrity

## 🎉 **Conclusion**

The Before/After Photo System provides a robust foundation for visual documentation in property management. With proper categorization, approval workflows, and flexible querying, it enables comprehensive photo management that scales with business needs.

The system maintains data integrity through constraints while providing the flexibility needed for various property management scenarios. The comprehensive test suite ensures reliability and the clear documentation supports easy adoption and maintenance.
