# Calendar Implementation Guide

## 📅 Overview

The Aristay Calendar system provides a unified view of all bookings and tasks in a comprehensive calendar interface. This implementation integrates seamlessly with the existing portal system and provides both API endpoints and web-based calendar views.

## 🏗️ Architecture

### Core Components

1. **API Layer** (`api/calendar_views.py`)
   - DRF ViewSet for calendar events
   - Unified task and booking data aggregation
   - Permission-based filtering

2. **Django Views** (`api/calendar_django_views.py`)
   - HTML calendar rendering
   - AJAX endpoints for filters and data
   - Portal integration

3. **Serializers** (`api/calendar_serializers.py`)
   - Calendar-specific data formatting
   - URL generation for detail pages
   - FullCalendar.js compatibility

4. **Templates**
   - `templates/calendar/calendar_view.html` - Standalone calendar
   - `templates/portal/calendar.html` - Portal-integrated calendar

## 🚀 Features

### ✅ Implemented Features

#### **1. Unified Calendar Display**
- **FullCalendar.js Integration**: Modern, responsive calendar interface
- **Event Types**: Tasks (blue) and Bookings (green) with distinct styling
- **Multiple Views**: Month, week, day, and list views
- **Real-time Updates**: Dynamic event loading and refresh

#### **2. Portal Integration**
- **Portal Home Card**: Easy access from main portal page
- **Navigation Menu**: Calendar link in portal navigation
- **Consistent Styling**: Matches portal design system
- **User Context**: Role-based permissions and data filtering

#### **3. Advanced Filtering**
- **Property Filter**: Filter events by specific properties
- **Status Filter**: Filter by task/booking status
- **User Filter**: Filter by assigned user
- **Date Range**: Automatic date range filtering

#### **4. Event Interaction**
- **Click Handlers**: Click events to view details
- **Modal Display**: Event details in popup modals
- **Detail Navigation**: Direct links to task/booking detail pages
- **Hover Effects**: Visual feedback for interactive elements

#### **5. API Endpoints**
- **`/api/calendar/events/`** - Main calendar events endpoint
- **`/api/calendar/tasks/`** - Tasks-only endpoint
- **`/api/calendar/bookings/`** - Bookings-only endpoint
- **`/api/calendar/day_events/`** - Day-specific events
- **`/api/calendar/properties/`** - Property filter options
- **`/api/calendar/users/`** - User filter options
- **`/api/calendar/stats/`** - Calendar statistics

#### **6. Permission System**
- **Role-based Access**: Different views based on user roles
- **Data Filtering**: Users only see events they have permission to view
- **Security**: Proper authentication and authorization

## 📁 File Structure

```
aristay_backend/
├── api/
│   ├── calendar_views.py              # DRF API endpoints
│   ├── calendar_django_views.py       # Django HTML views
│   ├── calendar_serializers.py        # Data serializers
│   ├── templates/
│   │   ├── calendar/
│   │   │   └── calendar_view.html     # Standalone calendar
│   │   └── portal/
│   │       └── calendar.html          # Portal calendar
│   └── urls.py                        # URL routing
├── tests/
│   └── api/
│       └── test_calendar_api.py       # Comprehensive tests
└── scripts/
    └── testing/
        └── setup_test_db.sh           # Test database setup
```

## 🔧 Technical Implementation

### **1. Data Aggregation**

The calendar system aggregates data from two main sources:

```python
# Tasks
tasks = Task.objects.filter(
    due_date__date__range=[start_date, end_date],
    is_deleted=False
)

# Bookings
bookings = Booking.objects.filter(
    Q(check_in_date__date__lte=end_date) & 
    Q(check_out_date__date__gte=start_date),
    is_deleted=False
)
```

### **2. Event Serialization**

Events are serialized for FullCalendar.js compatibility:

```python
class CalendarEventSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField(allow_null=True)
    allDay = serializers.BooleanField()
    type = serializers.CharField()  # 'task' or 'booking'
    status = serializers.CharField()
    color = serializers.CharField()
    url = serializers.CharField(allow_null=True)
```

### **3. Permission Integration**

The calendar respects existing permission systems:

```python
def get_queryset_tasks(self, user, filters=None):
    """Get tasks based on user permissions"""
    if user.is_superuser:
        return Task.objects.filter(is_deleted=False)
    
    # Apply role-based filtering
    if hasattr(user, 'profile'):
        if not user.profile.has_permission('view_all_tasks'):
            return Task.objects.filter(
                Q(assigned_to=user) | Q(created_by=user),
                is_deleted=False
            )
```

## 🌐 URL Patterns

### **Portal URLs**
- `/api/portal/calendar/` - Portal calendar view
- `/api/portal/` - Portal home (with calendar card)

### **API URLs**
- `/api/calendar/events/` - Main events endpoint
- `/api/calendar/tasks/` - Tasks endpoint
- `/api/calendar/bookings/` - Bookings endpoint
- `/api/calendar/day_events/` - Day events endpoint
- `/api/calendar/properties/` - Properties filter
- `/api/calendar/users/` - Users filter
- `/api/calendar/stats/` - Statistics endpoint

### **Standalone URLs**
- `/api/calendar/` - Standalone calendar view

## 🎨 Frontend Implementation

### **1. FullCalendar.js Integration**

```javascript
calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
    },
    events: function(info, successCallback, failureCallback) {
        loadCalendarEvents(info.start, info.end, successCallback, failureCallback);
    },
    eventClick: function(info) {
        info.jsEvent.preventDefault();
        showEventDetails(info.event);
    }
});
```

### **2. Event Styling**

```css
.event-task {
    border-left: 4px solid #007bff;
    background-color: #f8f9ff;
}

.event-booking {
    border-left: 4px solid #28a745;
    background-color: #f8fff8;
}
```

### **3. Responsive Design**

The calendar is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones
- Different screen orientations

## 🔐 Security Features

### **1. Authentication**
- All calendar endpoints require authentication
- JWT token-based authentication
- Session-based authentication for HTML views

### **2. Authorization**
- Role-based access control
- Permission-based data filtering
- User-specific event visibility

### **3. Data Protection**
- SQL injection prevention
- XSS protection
- CSRF protection for forms

## 🧪 Testing

### **Test Coverage**

The calendar implementation includes comprehensive tests:

```python
# API Tests
- test_calendar_events_endpoint
- test_calendar_tasks_endpoint
- test_calendar_bookings_endpoint
- test_calendar_day_events_endpoint
- test_calendar_events_with_filters
- test_calendar_events_permission_filtering

# HTML Tests
- test_calendar_view_authenticated
- test_calendar_view_unauthorized
- test_calendar_properties_api
- test_calendar_users_api

# Serializer Tests
- test_calendar_event_serializer
```

### **Test Database Setup**

```bash
# Setup test database with required extensions
./scripts/testing/setup_test_db.sh
```

## 🚀 Usage Guide

### **1. Accessing the Calendar**

#### **Via Portal Home**
1. Navigate to `/api/portal/`
2. Click the "📅 Calendar View" card
3. Click "Open Calendar" button

#### **Via Navigation Menu**
1. Navigate to `/api/portal/`
2. Click "📅 Calendar" in the navigation menu

#### **Direct Access**
1. Navigate directly to `/api/portal/calendar/`

### **2. Using the Calendar**

#### **Viewing Events**
- **Month View**: See all events for the month
- **Week View**: Detailed week view
- **Day View**: Hour-by-hour day view
- **List View**: Chronological list of events

#### **Filtering Events**
1. Use the filter panel at the top
2. Select property, status, or user filters
3. Click "Apply Filters" to update the view
4. Click "Clear" to reset all filters

#### **Interacting with Events**
- **Click Event**: View event details in modal
- **Click Date**: View all events for that day
- **Hover Event**: See event preview

### **3. Event Details**

When you click on an event, you'll see:
- Event title and description
- Event type (task or booking)
- Status information
- Property details
- Assigned user (for tasks)
- Guest information (for bookings)
- Date and time information
- Link to detailed view

## 🔧 Configuration

### **1. Environment Variables**

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aristay_local

# JWT Settings
JWT_SIGNING_KEY=your-secret-key

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### **2. Django Settings**

```python
# Calendar-specific settings
CALENDAR_SETTINGS = {
    'DEFAULT_VIEW': 'dayGridMonth',
    'EVENTS_PER_PAGE': 100,
    'CACHE_TIMEOUT': 300,  # 5 minutes
}
```

## 🐛 Troubleshooting

### **Common Issues**

#### **1. Calendar Not Loading**
- Check if user is authenticated
- Verify database connection
- Check browser console for JavaScript errors

#### **2. Events Not Showing**
- Verify user permissions
- Check if events exist in the database
- Verify date range filters

#### **3. Filter Not Working**
- Check if filter options are loaded
- Verify API endpoint responses
- Check browser network tab for errors

#### **4. Permission Errors**
- Verify user role and permissions
- Check if user has access to properties
- Verify task/booking assignments

### **Debug Mode**

Enable debug mode for detailed error information:

```python
DEBUG = True
```

## 📈 Performance Considerations

### **1. Database Optimization**
- Indexed date fields for fast queries
- Pagination for large datasets
- Caching for frequently accessed data

### **2. Frontend Optimization**
- Lazy loading of events
- Efficient DOM updates
- Minimal API calls

### **3. Caching Strategy**
- Redis caching for API responses
- Browser caching for static assets
- CDN for external libraries

## 🔮 Future Enhancements

### **Planned Features**
- **Export Functionality**: PDF/Excel export
- **Print Support**: Print-friendly views
- **Mobile Optimization**: Touch gestures
- **Real-time Updates**: WebSocket integration
- **Calendar Sharing**: Share with other users
- **Recurring Events**: Support for recurring tasks
- **Event Templates**: Quick event creation

### **Advanced Features**
- **Drag & Drop**: Move events between dates
- **Bulk Operations**: Select multiple events
- **Advanced Filtering**: Custom filter combinations
- **Calendar Sync**: External calendar integration
- **Notifications**: Event reminders and alerts

## 📚 API Reference

### **GET /api/calendar/events/**

Returns calendar events for a date range.

**Parameters:**
- `start_date` (string): Start date (YYYY-MM-DD)
- `end_date` (string): End date (YYYY-MM-DD)
- `property_id` (int): Filter by property
- `status` (string): Filter by status
- `user_id` (int): Filter by assigned user

**Response:**
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
  }
]
```

### **GET /api/calendar/day_events/**

Returns events for a specific day.

**Parameters:**
- `date` (string): Date (YYYY-MM-DD)

**Response:**
```json
{
  "date": "2025-01-15",
  "tasks": [...],
  "bookings": [...],
  "events": [...],
  "total_events": 5
}
```

## 🎯 Conclusion

The Aristay Calendar implementation provides a comprehensive, user-friendly interface for managing property bookings and tasks. With its seamless portal integration, advanced filtering capabilities, and robust permission system, it serves as a central hub for property management operations.

The implementation follows Django best practices, includes comprehensive testing, and provides a solid foundation for future enhancements. The calendar is production-ready and provides an excellent user experience across all devices.

---

**Last Updated**: September 17, 2025  
**Version**: 1.0.0  
**Status**: Production Ready ✅
