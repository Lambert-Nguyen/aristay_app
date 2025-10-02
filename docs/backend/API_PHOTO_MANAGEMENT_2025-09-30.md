# Photo Management API Documentation

**Date**: September 30, 2025  
**API Version**: 1.0.0  
**Base URL**: `/api/`

## Overview

The Photo Management API provides comprehensive endpoints for managing photos across all tasks in the AriStay platform. This API supports photo upload, retrieval, status management, and approval workflows.

## Authentication

All API endpoints require authentication using JWT tokens or session authentication.

```http
Authorization: Bearer <jwt_token>
```

## Base URL Structure

```
/api/tasks/{task_id}/images/
```

## Endpoints

### 1. List Photos for Task

**GET** `/api/tasks/{task_id}/images/`

Retrieves all photos associated with a specific task.

#### Parameters
- `task_id` (path, required): Task ID
- `photo_status` (query, optional): Filter by status (pending, approved, rejected, archived)
- `photo_type` (query, optional): Filter by type (before, after, checklist)
- `page` (query, optional): Page number for pagination
- `page_size` (query, optional): Number of items per page

#### Response
```json
{
    "count": 15,
    "next": "http://localhost:8000/api/tasks/123/images/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "task": 123,
            "checklist_response": 456,
            "image": "https://example.com/media/task_images/photo1.jpg",
            "photo_type": "before",
            "photo_status": "pending",
            "photo_type_display": "Before",
            "photo_status_display": "Pending",
            "sequence_number": 1,
            "description": "Kitchen before cleaning",
            "created_at": "2025-09-30T10:30:00Z",
            "updated_at": "2025-09-30T10:30:00Z"
        }
    ]
}
```

#### Status Codes
- `200 OK`: Photos retrieved successfully
- `404 Not Found`: Task not found
- `403 Forbidden`: Insufficient permissions

### 2. Upload Photo to Task

**POST** `/api/tasks/{task_id}/images/`

Uploads a new photo to a specific task.

#### Parameters
- `task_id` (path, required): Task ID
- `image` (form-data, required): Photo file
- `photo_type` (form-data, required): Type of photo (before, after, checklist)
- `description` (form-data, optional): Photo description
- `checklist_response` (form-data, optional): Checklist response ID (for checklist photos)

#### Request Example
```bash
curl -X POST \
  http://localhost:8000/api/tasks/123/images/ \
  -H 'Authorization: Bearer <token>' \
  -F 'image=@photo.jpg' \
  -F 'photo_type=before' \
  -F 'description=Kitchen before cleaning'
```

#### Response
```json
{
    "id": 1,
    "task": 123,
    "checklist_response": null,
    "image": "https://example.com/media/task_images/photo1.jpg",
    "photo_type": "before",
    "photo_status": "pending",
    "photo_type_display": "Before",
    "photo_status_display": "Pending",
    "sequence_number": 1,
    "description": "Kitchen before cleaning",
    "created_at": "2025-09-30T10:30:00Z",
    "updated_at": "2025-09-30T10:30:00Z"
}
```

#### Status Codes
- `201 Created`: Photo uploaded successfully
- `400 Bad Request`: Invalid file or parameters
- `413 Payload Too Large`: File size exceeds limit
- `403 Forbidden`: Insufficient permissions

### 3. Retrieve Specific Photo

**GET** `/api/tasks/{task_id}/images/{image_id}/`

Retrieves details for a specific photo.

#### Parameters
- `task_id` (path, required): Task ID
- `image_id` (path, required): Photo ID

#### Response
```json
{
    "id": 1,
    "task": 123,
    "checklist_response": 456,
    "image": "https://example.com/media/task_images/photo1.jpg",
    "photo_type": "before",
    "photo_status": "approved",
    "photo_type_display": "Before",
    "photo_status_display": "Approved",
    "sequence_number": 1,
    "description": "Kitchen before cleaning",
    "created_at": "2025-09-30T10:30:00Z",
    "updated_at": "2025-09-30T10:30:00Z"
}
```

#### Status Codes
- `200 OK`: Photo retrieved successfully
- `404 Not Found`: Photo or task not found
- `403 Forbidden`: Insufficient permissions

### 4. Update Photo Status

**PATCH** `/api/tasks/{task_id}/images/{image_id}/`

Updates the status of a specific photo (approve, reject, archive).

#### Parameters
- `task_id` (path, required): Task ID
- `image_id` (path, required): Photo ID
- `photo_status` (body, required): New status (pending, approved, rejected, archived)

#### Request Example
```bash
curl -X PATCH \
  http://localhost:8000/api/tasks/123/images/1/ \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"photo_status": "approved"}'
```

#### Response
```json
{
    "id": 1,
    "task": 123,
    "checklist_response": 456,
    "image": "https://example.com/media/task_images/photo1.jpg",
    "photo_type": "before",
    "photo_status": "approved",
    "photo_type_display": "Before",
    "photo_status_display": "Approved",
    "sequence_number": 1,
    "description": "Kitchen before cleaning",
    "created_at": "2025-09-30T10:30:00Z",
    "updated_at": "2025-09-30T10:30:00Z"
}
```

#### Status Codes
- `200 OK`: Photo status updated successfully
- `400 Bad Request`: Invalid status transition
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Photo or task not found

### 5. Delete Photo

**DELETE** `/api/tasks/{task_id}/images/{image_id}/`

Deletes a specific photo (soft delete).

#### Parameters
- `task_id` (path, required): Task ID
- `image_id` (path, required): Photo ID

#### Response
```json
{
    "message": "Photo deleted successfully"
}
```

#### Status Codes
- `204 No Content`: Photo deleted successfully
- `404 Not Found`: Photo or task not found
- `403 Forbidden`: Insufficient permissions

## Data Models

### TaskImage Model

```python
class TaskImage(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    checklist_response = models.ForeignKey(ChecklistResponse, null=True, blank=True)
    image = models.ImageField(upload_to='task_images/')
    photo_type = models.CharField(max_length=20, choices=PHOTO_TYPE_CHOICES)
    photo_status = models.CharField(max_length=20, choices=PHOTO_STATUS_CHOICES)
    sequence_number = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
```

### Photo Type Choices

```python
PHOTO_TYPE_CHOICES = [
    ('before', 'Before'),
    ('after', 'After'),
    ('checklist', 'Checklist'),
]
```

### Photo Status Choices

```python
PHOTO_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('archived', 'Archived'),
]
```

## Status Transition Rules

### Valid Transitions

| Current Status | Allowed Transitions |
|----------------|-------------------|
| `pending` | `approved`, `rejected` |
| `approved` | `archived`, `rejected` |
| `rejected` | `pending`, `archived`, `approved` |
| `archived` | `pending`, `approved`, `rejected` |

### Business Rules

1. **Pending Photos**: Newly uploaded photos start in pending status
2. **Approval Required**: Only managers/superusers can approve photos
3. **Status Changes**: All status changes are logged in audit trail
4. **Notifications**: Status changes trigger notifications to relevant users

## Error Handling

### Error Response Format

```json
{
    "error": "Error message",
    "detail": "Detailed error description",
    "field_errors": {
        "field_name": ["Field-specific error message"]
    }
}
```

### Common Error Scenarios

#### 400 Bad Request
```json
{
    "error": "Invalid file type",
    "detail": "Only JPEG, PNG, and MPO files are allowed"
}
```

#### 403 Forbidden
```json
{
    "error": "Permission denied",
    "detail": "You do not have permission to perform this action"
}
```

#### 404 Not Found
```json
{
    "error": "Not found",
    "detail": "Photo with ID 123 not found"
}
```

#### 413 Payload Too Large
```json
{
    "error": "File too large",
    "detail": "File size exceeds maximum limit of 25MB"
}
```

## Rate Limiting

### Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Photo Upload | 15 requests | 1 minute |
| Photo Status Update | 30 requests | 1 minute |
| Photo List | 100 requests | 1 hour |

### Rate Limit Headers

```http
X-RateLimit-Limit: 15
X-RateLimit-Remaining: 14
X-RateLimit-Reset: 1640995200
```

## File Upload Specifications

### Supported File Types
- **JPEG** (.jpg, .jpeg)
- **PNG** (.png)
- **MPO** (.mpo) - Multi Picture Object

### File Size Limits
- **Maximum Size**: 25MB per file
- **Recommended Size**: 1-5MB for optimal performance
- **Minimum Resolution**: 800x600 pixels

### File Validation
```python
def validate_image_file(file):
    """Validate uploaded image file"""
    # Check file size
    if file.size > settings.MAX_UPLOAD_BYTES:
        raise ValidationError("File too large")
    
    # Check file type
    allowed_types = ['image/jpeg', 'image/png', 'image/mpo']
    if file.content_type not in allowed_types:
        raise ValidationError("Invalid file type")
    
    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.mpo']
    if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
        raise ValidationError("Invalid file extension")
```

## Pagination

### Pagination Parameters
- `page`: Page number (1-based)
- `page_size`: Items per page (default: 20, max: 100)

### Pagination Response
```json
{
    "count": 150,
    "next": "http://localhost:8000/api/tasks/123/images/?page=3",
    "previous": "http://localhost:8000/api/tasks/123/images/?page=1",
    "results": [...]
}
```

## Filtering and Searching

### Available Filters

#### Photo Status Filter
```http
GET /api/tasks/123/images/?photo_status=pending
```

#### Photo Type Filter
```http
GET /api/tasks/123/images/?photo_type=before
```

#### Combined Filters
```http
GET /api/tasks/123/images/?photo_status=approved&photo_type=after
```

### Search Parameters
- `search`: Search in photo descriptions
- `created_after`: Filter by creation date
- `created_before`: Filter by creation date

## Webhooks (Future Enhancement)

### Photo Status Change Webhook
```json
{
    "event": "photo.status_changed",
    "data": {
        "photo_id": 123,
        "task_id": 456,
        "old_status": "pending",
        "new_status": "approved",
        "changed_by": "manager@example.com",
        "timestamp": "2025-09-30T10:30:00Z"
    }
}
```

## SDK Examples

### Python SDK
```python
import requests

class PhotoManagementAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def upload_photo(self, task_id, image_path, photo_type, description=None):
        url = f"{self.base_url}/api/tasks/{task_id}/images/"
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'photo_type': photo_type}
            if description:
                data['description'] = description
            
            response = requests.post(url, headers=self.headers, files=files, data=data)
            return response.json()
    
    def update_photo_status(self, task_id, image_id, status):
        url = f"{self.base_url}/api/tasks/{task_id}/images/{image_id}/"
        data = {'photo_status': status}
        response = requests.patch(url, headers=self.headers, json=data)
        return response.json()
```

### JavaScript SDK
```javascript
class PhotoManagementAPI {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }
    
    async uploadPhoto(taskId, imageFile, photoType, description = null) {
        const formData = new FormData();
        formData.append('image', imageFile);
        formData.append('photo_type', photoType);
        if (description) {
            formData.append('description', description);
        }
        
        const response = await fetch(`${this.baseUrl}/api/tasks/${taskId}/images/`, {
            method: 'POST',
            headers: {
                'Authorization': this.headers.Authorization
            },
            body: formData
        });
        
        return await response.json();
    }
    
    async updatePhotoStatus(taskId, imageId, status) {
        const response = await fetch(`${this.baseUrl}/api/tasks/${taskId}/images/${imageId}/`, {
            method: 'PATCH',
            headers: this.headers,
            body: JSON.stringify({ photo_status: status })
        });
        
        return await response.json();
    }
}
```

## Testing

### Test Endpoints
```bash
# Test photo upload
curl -X POST http://localhost:8000/api/tasks/123/images/ \
  -H 'Authorization: Bearer <token>' \
  -F 'image=@test.jpg' \
  -F 'photo_type=before'

# Test status update
curl -X PATCH http://localhost:8000/api/tasks/123/images/1/ \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"photo_status": "approved"}'

# Test photo list
curl -X GET http://localhost:8000/api/tasks/123/images/ \
  -H 'Authorization: Bearer <token>'
```

### Postman Collection
A Postman collection is available for testing all endpoints:
- Import the collection from `/docs/api/Photo_Management_API.postman_collection.json`
- Set up environment variables for base URL and authentication token
- Run the collection to test all endpoints

## Changelog

### Version 1.0.0 (2025-09-30)
- Initial release of Photo Management API
- Support for photo upload, retrieval, and status management
- Role-based access control
- Comprehensive error handling
- Rate limiting implementation

## Support

For API support and questions:
- **Documentation**: `/docs/api/`
- **Issue Tracker**: GitHub Issues
- **Email**: api-support@aristay.com
- **Slack**: #api-support channel

## Conclusion

The Photo Management API provides a robust, secure, and scalable solution for managing photos across the AriStay platform. The API is designed with developer experience in mind, offering comprehensive documentation, clear error messages, and consistent response formats.

**Key Features:**
- ✅ RESTful API design
- ✅ Comprehensive error handling
- ✅ Rate limiting and security
- ✅ Detailed documentation
- ✅ SDK examples and testing tools

The API is production-ready and provides a solid foundation for photo management functionality.

