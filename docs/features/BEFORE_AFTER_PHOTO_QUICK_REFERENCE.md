# 📸 Before/After Photo System - Quick Reference

**Last Updated**: September 10, 2025

## 🎯 **Quick Overview**

The Before/After Photo System allows property management staff to categorize, organize, and manage photos with approval workflows for comprehensive visual documentation.

## 📋 **Photo Types**

| Type | Description | Use Case |
|------|-------------|----------|
| `before` | Initial state | Property condition before work |
| `after` | Completed work | Property condition after work |
| `during` | Work in progress | Mid-work documentation |
| `reference` | General reference | Setup, equipment, context |
| `damage` | Damage documentation | Issues, repairs needed |
| `general` | Miscellaneous | Other photos |

## 🔄 **Photo Status Workflow**

```
Pending Review → Approved/Rejected → Archived
```

| Status | Description | Action Required |
|--------|-------------|-----------------|
| `pending` | Newly uploaded | Manager review |
| `approved` | Accepted | Ready for use |
| `rejected` | Not suitable | Re-upload needed |
| `archived` | Moved to archive | Historical reference |

## 💻 **API Usage**

### **Upload Photo**
```python
POST /api/task-images/
{
    "task": 123,
    "image": <file>,
    "photo_type": "before",
    "description": "Property before cleaning",
    "sequence_number": 1
}
```

### **Update Photo Status**
```python
PATCH /api/task-images/{id}/
{
    "photo_status": "approved"
}
```

### **Get Photos by Type**
```python
GET /api/task-images/?task=123&photo_type=before
GET /api/task-images/?task=123&photo_type=after
```

## 🔍 **Query Examples**

### **Get Before/After Pairs**
```python
# Before photos
before_photos = TaskImage.objects.filter(
    task=task,
    photo_type='before'
).order_by('sequence_number')

# After photos  
after_photos = TaskImage.objects.filter(
    task=task,
    photo_type='after'
).order_by('sequence_number')
```

### **Get Primary Photos**
```python
# All primary photos for a task
primary_photos = TaskImage.objects.filter(
    task=task,
    is_primary=True
)
```

### **Get Photos for Booking**
```python
# All photos for a booking
booking_photos = TaskImage.objects.filter(
    task__booking=booking
)
```

## 🏷️ **Key Features**

### **Automatic Primary Assignment**
- First photo of each type becomes primary automatically
- Only one primary photo per type per task
- Primary photos are marked with `is_primary=True`

### **Sequence Numbering**
- Photos within same type are numbered sequentially
- Use `sequence_number` for ordering
- Default is 1 for first photo

### **Rich Descriptions**
- Add detailed descriptions to photos
- Use `description` field for context
- Helpful for photo organization and search

## 📊 **Common Use Cases**

### **Cleaning Task Documentation**
1. Upload `before` photos showing initial state
2. Upload `during` photos showing work progress
3. Upload `after` photos showing completed work
4. Manager reviews and approves photos
5. Photos are organized by sequence for comparison

### **Maintenance Task Documentation**
1. Upload `damage` photos showing issues
2. Upload `reference` photos showing equipment/setup
3. Upload `during` photos showing repair work
4. Upload `after` photos showing completed repairs

### **Property Inspection**
1. Upload `reference` photos of each room/area
2. Upload `damage` photos of any issues found
3. Upload `before` photos before any work
4. Upload `after` photos after work completion

## 🚀 **Best Practices**

### **Photo Organization**
- Use consistent sequence numbers (1, 2, 3...)
- Add descriptive text in `description` field
- Upload photos in logical order
- Use appropriate photo types

### **Approval Workflow**
- Review photos promptly
- Approve good quality photos
- Reject photos that don't meet standards
- Archive old photos when no longer needed

### **Query Performance**
- Use specific filters (task, photo_type, status)
- Leverage database indexes for fast queries
- Use `select_related` for task/booking data

## 🔧 **Technical Notes**

### **Database Constraints**
- Unique constraint: `(task, photo_type, sequence_number)`
- Only one primary photo per type per task
- Sequence numbers must be positive

### **Model Fields**
- `photo_type`: Choice field with 6 options
- `photo_status`: Choice field with 4 options
- `sequence_number`: Positive integer for ordering
- `is_primary`: Boolean for primary designation
- `description`: Text field for detailed descriptions

### **Indexes**
- `(task, photo_type)` for type-based queries
- `photo_status` for status-based queries
- `uploaded_at` for time-based queries

## 📚 **Related Documentation**

- [`BEFORE_AFTER_PHOTO_SYSTEM_2025-09-10.md`](./BEFORE_AFTER_PHOTO_SYSTEM_2025-09-10.md) - Complete implementation details
- [`TASK_GROUPS.md`](./TASK_GROUPS.md) - Task management system
- [`UI_UX_IMPROVEMENTS.md`](./UI_UX_IMPROVEMENTS.md) - User interface enhancements

## 🎉 **Quick Start**

1. **Create Task**: Set up a cleaning or maintenance task
2. **Upload Before Photos**: Use `photo_type='before'`
3. **Upload After Photos**: Use `photo_type='after'`
4. **Review Photos**: Check `photo_status='pending'`
5. **Approve Photos**: Update status to `'approved'`
6. **Query Photos**: Use filters to get organized photo sets

The Before/After Photo System provides powerful visual documentation capabilities for property management with a simple, intuitive API and flexible querying options.
