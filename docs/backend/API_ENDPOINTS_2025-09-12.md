# Aristay Property Management - API Endpoints Documentation

**Date:** September 12, 2025  
**API Version:** 2.0  
**Base URL:** `https://api.aristay.com/api` (Production)  
**Development URL:** `http://127.0.0.1:8000/api` (Local Development)

## Authentication

All API endpoints require JWT authentication unless otherwise specified. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Authentication Endpoints

#### POST /api/token/
Obtain JWT access and refresh tokens.

**Request Body:**
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST /api/token/refresh/
Refresh expired access token using refresh token.

**Request Body:**
```json
{
    "refresh": "your_refresh_token"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST /api/token/revoke/
Revoke (blacklist) a refresh token.

**Request Body:**
```json
{
    "refresh": "your_refresh_token"
}
```

**Response:**
```json
{
    "detail": "Token revoked"
}
```

## User Registration

#### POST /api/register/
Register a new user with invite code.

**Request Body:**
```json
{
    "username": "newuser",
    "email": "user@example.com",
    "password": "securepassword",
    "password_confirm": "securepassword",
    "first_name": "John",
    "last_name": "Doe",
    "invite_code": "INV123456"
}
```

**Response:**
```json
{
    "id": 123,
    "username": "newuser",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile": {
        "task_group": "general",
        "role": "member"
    }
}
```

#### POST /api/validate-invite/
Validate an invite code before registration.

**Request Body:**
```json
{
    "code": "INV123456"
}
```

**Response:**
```json
{
    "valid": true,
    "task_group": "general",
    "role": "member",
    "expires_at": "2025-12-31T23:59:59Z"
}
```

## Task Management

#### GET /api/staff/tasks/
Get list of tasks (filtered by user role).

**Query Parameters:**
- `status`: Filter by task status (pending, in-progress, completed)
- `task_type`: Filter by task type (cleaning, maintenance, laundry)
- `assigned_to`: Filter by assigned user ID
- `property`: Filter by property ID

**Response:**
```json
{
    "count": 25,
    "next": "http://api.aristay.com/api/staff/tasks/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Clean Room 101",
            "description": "Standard cleaning checklist",
            "status": "pending",
            "task_type": "cleaning",
            "priority": "medium",
            "assigned_to": 123,
            "assigned_to_username": "john_doe",
            "property": 1,
            "property_name": "Main Building",
            "due_date": "2025-09-15T10:00:00Z",
            "created_at": "2025-09-12T08:00:00Z",
            "checklist_id": 1,
            "checklist_template": "Standard Cleaning Checklist",
            "checklist_progress": {
                "percentage": 0,
                "completed": 0,
                "total": 5,
                "remaining": 5
            }
        }
    ]
}
```

#### GET /api/staff/tasks/{id}/
Get detailed information about a specific task.

**Response:**
```json
{
    "id": 1,
    "title": "Clean Room 101",
    "description": "Standard cleaning checklist",
    "status": "pending",
    "task_type": "cleaning",
    "priority": "medium",
    "assigned_to": 123,
    "assigned_to_username": "john_doe",
    "property": 1,
    "property_name": "Main Building",
    "due_date": "2025-09-15T10:00:00Z",
    "created_at": "2025-09-12T08:00:00Z",
    "checklist": {
        "id": 1,
        "template": "Standard Cleaning Checklist",
        "items": [
            {
                "id": 1,
                "text": "Vacuum carpet",
                "completed": false,
                "completed_at": null
            },
            {
                "id": 2,
                "text": "Clean bathroom",
                "completed": true,
                "completed_at": "2025-09-12T09:30:00Z"
            }
        ]
    },
    "images": [
        {
            "id": 1,
            "image": "https://api.aristay.com/media/task_images/image1.jpg",
            "photo_type": "before",
            "uploaded_at": "2025-09-12T08:15:00Z"
        }
    ]
}
```

#### PATCH /api/staff/tasks/{id}/
Update task status or other fields.

**Request Body:**
```json
{
    "status": "in-progress",
    "notes": "Started cleaning, found some issues"
}
```

**Response:**
```json
{
    "id": 1,
    "status": "in-progress",
    "notes": "Started cleaning, found some issues",
    "updated_at": "2025-09-12T10:30:00Z"
}
```

#### GET /api/staff/tasks/{id}/progress/
Get task checklist progress.

**Response:**
```json
{
    "percentage": 40,
    "completed": 2,
    "total": 5,
    "remaining": 3
}
```

## Photo Upload

#### POST /api/tasks/{task_id}/images/create/
Upload a photo for a specific task.

**Request Body:** (multipart/form-data)
- `image`: Image file
- `task`: Task ID (integer)
- `photo_type`: Type of photo (before, after, general, reference)
- `description`: Optional description

**Response:**
```json
{
    "id": 1,
    "image": "https://api.aristay.com/media/task_images/image1.jpg",
    "photo_type": "before",
    "photo_type_display": "Before Photo",
    "photo_status": "pending",
    "photo_status_display": "Pending Review",
    "sequence_number": 1,
    "is_primary": false,
    "description": "Initial room condition",
    "uploaded_at": "2025-09-12T10:30:00Z",
    "uploaded_by": 123,
    "uploaded_by_username": "john_doe",
    "size_bytes": 1024000,
    "width": 1920,
    "height": 1080
}
```

#### GET /api/tasks/{task_id}/images/
Get all photos for a specific task.

**Response:**
```json
{
    "count": 3,
    "results": [
        {
            "id": 1,
            "image": "https://api.aristay.com/media/task_images/image1.jpg",
            "photo_type": "before",
            "uploaded_at": "2025-09-12T10:30:00Z"
        }
    ]
}
```

## Staff Dashboard

#### GET /api/staff/dashboard/
Get staff dashboard data including task counts and recent activity.

**Response:**
```json
{
    "task_counts": {
        "total": 25,
        "pending": 8,
        "in_progress": 12,
        "completed": 5
    },
    "recent_tasks": [
        {
            "id": 1,
            "title": "Clean Room 101",
            "status": "pending",
            "due_date": "2025-09-15T10:00:00Z"
        }
    ],
    "notifications": [
        {
            "id": 1,
            "message": "New task assigned: Clean Room 102",
            "created_at": "2025-09-12T09:00:00Z",
            "is_read": false
        }
    ]
}
```

#### GET /api/staff/task-counts/
Get real-time task counts for dashboard updates.

**Response:**
```json
{
    "total": 25,
    "pending": 8,
    "in_progress": 12,
    "completed": 5
}
```

## Property Management

#### GET /api/properties/
Get list of properties.

**Response:**
```json
{
    "count": 5,
    "results": [
        {
            "id": 1,
            "name": "Main Building",
            "address": "123 Main St, City, State",
            "property_type": "apartment",
            "total_units": 50,
            "active_units": 45
        }
    ]
}
```

#### GET /api/properties/{id}/
Get detailed property information.

**Response:**
```json
{
    "id": 1,
    "name": "Main Building",
    "address": "123 Main St, City, State",
    "property_type": "apartment",
    "total_units": 50,
    "active_units": 45,
    "units": [
        {
            "id": 1,
            "unit_number": "101",
            "status": "occupied",
            "current_booking": {
                "id": 1,
                "guest_name": "John Doe",
                "check_in": "2025-09-10T15:00:00Z",
                "check_out": "2025-09-15T11:00:00Z"
            }
        }
    ]
}
```

## Booking Management

#### POST /api/bookings/import/
Import bookings from Excel/CSV file.

**Request Body:** (multipart/form-data)
- `file`: Excel/CSV file
- `property_id`: Property ID for the bookings

**Response:**
```json
{
    "import_id": "imp_123456",
    "status": "processing",
    "total_rows": 100,
    "processed_rows": 0,
    "conflicts_found": 5,
    "conflicts": [
        {
            "row_number": 10,
            "conflict_type": "duplicate_booking",
            "existing_booking": {
                "id": 1,
                "external_code": "AIR123456"
            },
            "new_booking": {
                "external_code": "AIR123456",
                "guest_name": "John Doe"
            }
        }
    ]
}
```

#### GET /api/bookings/
Get list of bookings.

**Query Parameters:**
- `property`: Filter by property ID
- `status`: Filter by booking status
- `check_in_date`: Filter by check-in date
- `check_out_date`: Filter by check-out date

**Response:**
```json
{
    "count": 50,
    "results": [
        {
            "id": 1,
            "external_code": "AIR123456",
            "source": "airbnb",
            "guest_name": "John Doe",
            "check_in_date": "2025-09-10T15:00:00Z",
            "check_out_date": "2025-09-15T11:00:00Z",
            "property": 1,
            "property_name": "Main Building",
            "unit": "101",
            "status": "confirmed",
            "total_nights": 5,
            "created_at": "2025-09-12T08:00:00Z"
        }
    ]
}
```

## Admin Management

#### GET /api/admin/invite-codes/
Get list of invite codes (admin only).

**Response:**
```json
{
    "count": 10,
    "results": [
        {
            "id": 1,
            "code": "INV123456",
            "task_group": "general",
            "role": "member",
            "max_uses": 1,
            "used_count": 0,
            "expires_at": "2025-12-31T23:59:59Z",
            "is_active": true,
            "created_at": "2025-09-12T08:00:00Z"
        }
    ]
}
```

#### POST /api/admin/create-invite-code/
Create a new invite code (admin only).

**Request Body:**
```json
{
    "task_group": "general",
    "role": "member",
    "max_uses": 1,
    "expires_at": "2025-12-31T23:59:59Z",
    "notes": "General staff invite"
}
```

**Response:**
```json
{
    "id": 1,
    "code": "INV123456",
    "task_group": "general",
    "role": "member",
    "max_uses": 1,
    "used_count": 0,
    "expires_at": "2025-12-31T23:59:59Z",
    "is_active": true,
    "created_at": "2025-09-12T08:00:00Z"
}
```

## Error Responses

### 400 Bad Request
```json
{
    "error": "Validation failed",
    "details": {
        "field_name": ["This field is required."]
    }
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "error": "Permission denied"
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```

### 429 Too Many Requests
```json
{
    "detail": "Request was throttled. Expected available in 60 seconds."
}
```

### 500 Internal Server Error
```json
{
    "error": "Internal server error",
    "detail": "An unexpected error occurred."
}
```

## Rate Limiting

The API implements rate limiting on sensitive endpoints:

- **Authentication**: 5 requests per minute per IP
- **Token Refresh**: 2 requests per minute per JWT ID
- **Photo Upload**: 15 requests per minute per user
- **General API**: 1000 requests per hour per user

## Pagination

List endpoints support pagination with the following query parameters:

- `page`: Page number (default: 1)
- `page_size`: Number of items per page (default: 20, max: 100)

## Filtering and Sorting

Many endpoints support filtering and sorting:

- **Filtering**: Use query parameters to filter results
- **Sorting**: Use `ordering` parameter (e.g., `?ordering=-created_at`)

## Webhooks

The API supports webhooks for real-time updates:

- **Task Status Changes**: Notify when task status changes
- **New Bookings**: Notify when new bookings are created
- **Photo Uploads**: Notify when photos are uploaded

## SDKs and Libraries

Official SDKs are available for:

- **Python**: `pip install aristay-sdk`
- **JavaScript/Node.js**: `npm install aristay-sdk`
- **Flutter**: Available in pub.dev

## Support

For API support and questions:

- **Documentation**: https://docs.aristay.com
- **Support Email**: api-support@aristay.com
- **Status Page**: https://status.aristay.com

---
*API Documentation generated on September 12, 2025*  
*API Version: 2.0*  
*Last Updated: September 12, 2025*
