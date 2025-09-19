# Calendar API Documentation

## 📋 Overview

This document provides comprehensive technical documentation for the Aristay Calendar API endpoints and implementation details.

## 🔗 Base URL

```
http://localhost:8003/api/calendar/
```

## 🔐 Authentication

All calendar endpoints require authentication. Use one of the following methods:

### JWT Token Authentication
```bash
Authorization: Bearer <your_jwt_token>
```

### Session Authentication
```bash
# For HTML views - login via Django admin or portal
# Session cookie will be automatically included
```

## 📊 API Endpoints

### 1. Calendar Events

#### `GET /api/calendar/events/`

Returns unified calendar events (tasks and bookings) for a date range.

**Query Parameters:**
- `start_date` (string, optional): Start date in YYYY-MM-DD format
- `end_date` (string, optional): End date in YYYY-MM-DD format
- `property_id` (int, optional): Filter by property ID
- `status` (string, optional): Filter by status
- `user_id` (int, optional): Filter by assigned user ID
- `include_tasks` (boolean, optional): Include tasks (default: true)
- `include_bookings` (boolean, optional): Include bookings (default: true)

**Response Format:**
```json
[
  {
    "id": "task_123",
    "title": "Clean Room 101",
    "start": "2025-01-15T09:00:00Z",
    "end": null,
    "allDay": true,
    "type": "task",
    "status": "pending",
    "color": "#007bff",
    "property_name": "Main Property",
    "assigned_to": "john_doe",
    "description": "Clean and prepare room for next guest",
    "url": "/api/tasks/123/"
  },
  {
    "id": "booking_456",
    "title": "Main Property - John Smith",
    "start": "2025-01-15T00:00:00Z",
    "end": "2025-01-17T00:00:00Z",
    "allDay": true,
    "type": "booking",
    "status": "confirmed",
    "color": "#28a745",
    "property_name": "Main Property",
    "guest_name": "John Smith",
    "description": "Booking from 2025-01-15 to 2025-01-17",
    "url": "/api/bookings/456/"
  }
]
```

**Status Codes:**
- `200 OK`: Events retrieved successfully
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `400 Bad Request`: Invalid parameters

### 2. Tasks Endpoint

#### `GET /api/calendar/tasks/`

Returns only task events for the calendar.

**Query Parameters:**
- `start_date` (string, optional): Start date in YYYY-MM-DD format
- `end_date` (string, optional): End date in YYYY-MM-DD format
- `property_id` (int, optional): Filter by property ID
- `status` (string, optional): Filter by task status
- `user_id` (int, optional): Filter by assigned user ID

**Response Format:**
```json
[
  {
    "id": 123,
    "title": "Clean Room 101",
    "description": "Clean and prepare room for next guest",
    "status": "pending",
    "status_display": "Pending",
    "due_date": "2025-01-15T09:00:00Z",
    "created_at": "2025-01-10T10:00:00Z",
    "property_ref": 1,
    "property_name": "Main Property",
    "assigned_to": 2,
    "assigned_to_username": "john_doe",
    "task_type": "cleaning",
    "url": "/api/tasks/123/"
  }
]
```

### 3. Bookings Endpoint

#### `GET /api/calendar/bookings/`

Returns only booking events for the calendar.

**Query Parameters:**
- `start_date` (string, optional): Start date in YYYY-MM-DD format
- `end_date` (string, optional): End date in YYYY-MM-DD format
- `property_id` (int, optional): Filter by property ID
- `status` (string, optional): Filter by booking status

**Response Format:**
```json
[
  {
    "id": 456,
    "property": 1,
    "property_name": "Main Property",
    "check_in_date": "2025-01-15T00:00:00Z",
    "check_out_date": "2025-01-17T00:00:00Z",
    "guest_name": "John Smith",
    "guest_contact": "john@example.com",
    "status": "confirmed",
    "status_display": "Confirmed",
    "external_code": "AIR123456",
    "tasks_count": 2,
    "url": "/api/bookings/456/"
  }
]
```

### 4. Day Events

#### `GET /api/calendar/day_events/`

Returns all events for a specific day.

**Query Parameters:**
- `date` (string, required): Date in YYYY-MM-DD format

**Response Format:**
```json
{
  "date": "2025-01-15",
  "tasks": [
    {
      "id": 123,
      "title": "Clean Room 101",
      "due_date": "2025-01-15T09:00:00Z",
      "status": "pending",
      "property_name": "Main Property",
      "assigned_to_username": "john_doe",
      "url": "/api/tasks/123/"
    }
  ],
  "bookings": [
    {
      "id": 456,
      "property_name": "Main Property",
      "guest_name": "John Smith",
      "check_in_date": "2025-01-15T00:00:00Z",
      "check_out_date": "2025-01-17T00:00:00Z",
      "status": "confirmed",
      "url": "/api/bookings/456/"
    }
  ],
  "events": [
    {
      "id": "task_123",
      "title": "Clean Room 101",
      "start": "2025-01-15T09:00:00Z",
      "allDay": true,
      "type": "task",
      "status": "pending",
      "color": "#007bff",
      "url": "/api/tasks/123/"
    }
  ],
  "total_events": 1
}
```

### 5. Properties Filter

#### `GET /api/calendar/properties/`

Returns available properties for filtering.

**Response Format:**
```json
[
  {
    "id": 1,
    "name": "Main Property",
    "address": "123 Main St"
  },
  {
    "id": 2,
    "name": "Beach House",
    "address": "456 Ocean Ave"
  }
]
```

### 6. Users Filter

#### `GET /api/calendar/users/`

Returns available users for filtering.

**Response Format:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "first_name": "Admin",
    "last_name": "User"
  },
  {
    "id": 2,
    "username": "john_doe",
    "first_name": "John",
    "last_name": "Doe"
  }
]
```

### 7. Statistics

#### `GET /api/calendar/stats/`

Returns calendar statistics.

**Response Format:**
```json
{
  "total_tasks": 25,
  "pending_tasks": 10,
  "in_progress_tasks": 8,
  "completed_tasks": 7,
  "total_bookings": 15,
  "active_bookings": 5,
  "week_tasks": 12,
  "month_tasks": 25
}
```

## 🔒 Permission System

### User Roles and Permissions

| Role | View Tasks | View All Tasks | View Bookings | Edit Events |
|------|------------|----------------|---------------|-------------|
| Superuser | ✅ | ✅ | ✅ | ✅ |
| Manager | ✅ | ✅ | ✅ | ✅ |
| Staff | ✅ | Own Only | ✅ | Own Only |
| Viewer | ❌ | ❌ | ✅ | ❌ |

### Permission Checks

```python
# Task permissions
if user.is_superuser:
    tasks = Task.objects.filter(is_deleted=False)
elif user.profile.has_permission('view_all_tasks'):
    tasks = Task.objects.filter(is_deleted=False)
else:
    tasks = Task.objects.filter(
        Q(assigned_to=user) | Q(created_by=user),
        is_deleted=False
    )

# Booking permissions
if user.is_superuser:
    bookings = Booking.objects.filter(is_deleted=False)
else:
    # Apply property access permissions
    accessible_properties = get_accessible_properties(user)
    bookings = Booking.objects.filter(
        property__in=accessible_properties,
        is_deleted=False
    )
```

## 🎨 Event Styling

### Task Events
- **Color**: `#007bff` (Blue)
- **Border**: Left border with task status
- **Icon**: Task-specific icon based on type

### Booking Events
- **Color**: `#28a745` (Green)
- **Border**: Left border with booking status
- **Icon**: Booking-specific icon

### Status Colors
- **Pending**: `#ffc107` (Yellow)
- **In Progress**: `#17a2b8` (Cyan)
- **Completed**: `#28a745` (Green)
- **Confirmed**: `#28a745` (Green)
- **Cancelled**: `#dc3545` (Red)

## 🔧 Error Handling

### Common Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### 400 Bad Request
```json
{
  "error": "Invalid date format. Use YYYY-MM-DD format."
}
```

#### 500 Internal Server Error
```json
{
  "error": "Internal server error. Please try again later."
}
```

## 📱 Frontend Integration

### FullCalendar.js Configuration

```javascript
const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
    },
    height: 'auto',
    events: function(info, successCallback, failureCallback) {
        loadCalendarEvents(info.start, info.end, successCallback, failureCallback);
    },
    eventClick: function(info) {
        info.jsEvent.preventDefault();
        showEventDetails(info.event);
    },
    eventDidMount: function(info) {
        if (info.event.extendedProps.type === 'task') {
            info.el.classList.add('event-task');
        } else if (info.event.extendedProps.type === 'booking') {
            info.el.classList.add('event-booking');
        }
    }
});
```

### Event Loading Function

```javascript
function loadCalendarEvents(start, end, successCallback, failureCallback) {
    const params = new URLSearchParams({
        start_date: start.toISOString().split('T')[0],
        end_date: end.toISOString().split('T')[0],
        ...currentFilters
    });

    fetch(`/api/calendar/events/?${params}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load events');
            }
            return response.json();
        })
        .then(events => {
            const processedEvents = events.map(event => {
                const { url, ...eventWithoutUrl } = event;
                return {
                    ...eventWithoutUrl,
                    extendedProps: {
                        ...eventWithoutUrl,
                        url: url
                    }
                };
            });
            successCallback(processedEvents);
        })
        .catch(error => {
            console.error('Error loading events:', error);
            failureCallback(error);
        });
}
```

## 🧪 Testing

### Test Database Setup

```bash
# Create test database with required extensions
./scripts/testing/setup_test_db.sh
```

### Running Tests

```bash
# Run all calendar tests
python -m pytest tests/api/test_calendar_api.py -v

# Run specific test
python -m pytest tests/api/test_calendar_api.py::CalendarAPITestCase::test_calendar_events_endpoint -v
```

### Test Coverage

- **API Endpoints**: All endpoints tested
- **Permission System**: Role-based access tested
- **Data Serialization**: Serializer validation tested
- **Error Handling**: Error responses tested
- **Frontend Integration**: HTML views tested

## 🚀 Performance Optimization

### Database Queries
- Indexed date fields for fast range queries
- Optimized JOIN operations
- Pagination for large datasets

### Caching Strategy
- Redis caching for API responses
- Browser caching for static assets
- CDN for external libraries

### Frontend Optimization
- Lazy loading of events
- Efficient DOM updates
- Minimal API calls

## 📊 Monitoring and Logging

### Logging
- API request/response logging
- Error logging with stack traces
- Performance metrics logging

### Monitoring
- Response time monitoring
- Error rate monitoring
- Database query performance

## 🔮 Future Enhancements

### Planned Features
- **Real-time Updates**: WebSocket integration
- **Export Functionality**: PDF/Excel export
- **Mobile Optimization**: Touch gestures
- **Calendar Sharing**: Share with other users
- **Recurring Events**: Support for recurring tasks

### API Versioning
- Version 1.0: Current implementation
- Version 1.1: Planned enhancements
- Backward compatibility maintained

---

**Last Updated**: September 17, 2025  
**API Version**: 1.0.0  
**Status**: Production Ready ✅
