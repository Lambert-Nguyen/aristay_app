# Invite Code Management System - Implementation Guide

**For System Administrators and Managers**  
**Last Updated:** September 13, 2025  
**Version:** 2.0

## 🎯 Overview

The Invite Code Management System provides comprehensive control over user registration by allowing administrators and managers to create, manage, and track invite codes. Each code automatically assigns users to specific roles and task groups upon registration, ensuring proper access control and organizational structure.

## 🏗️ System Architecture

### Core Components

1. **InviteCode Model** - Database model storing invite code information
2. **Management Views** - Web interfaces for both Admin and Manager portals
3. **API Endpoints** - RESTful APIs for programmatic access
4. **Permission System** - Role-based access control for invite code management
5. **Template System** - Responsive UI templates for all management interfaces

### Key Features

- ✅ **Dual Portal Access** - Both Admin and Manager portals
- ✅ **Role-Based Permissions** - Granular access control
- ✅ **Advanced Filtering** - Search and filter by role, task group, status
- ✅ **Usage Tracking** - Monitor code usage and expiration
- ✅ **Bulk Operations** - Create, edit, revoke, reactivate, delete codes
- ✅ **API Integration** - RESTful endpoints for external systems
- ✅ **Responsive Design** - Mobile-friendly interface
- ✅ **Audit Trail** - Complete activity logging

## 🔐 Access Control

### Permission Requirements

| User Role | Admin Portal | Manager Portal | API Access |
|-----------|-------------|----------------|------------|
| **Superuser** | ✅ Full Access | ✅ Full Access | ✅ Full Access |
| **Manager** | ❌ Denied | ✅ Full Access | ✅ Full Access |
| **Staff** | ❌ Denied | ❌ Denied | ❌ Denied |
| **Viewer** | ❌ Denied | ❌ Denied | ❌ Denied |

### Security Features

- **Permission Validation** - All endpoints verify user permissions
- **CSRF Protection** - All forms include CSRF tokens
- **Input Validation** - Comprehensive data validation
- **Rate Limiting** - API endpoints include rate limiting
- **Audit Logging** - All actions are logged for security

## 📋 User Interface

### Admin Portal (`/admin/invite-codes/`)

**Features:**
- Complete invite code management
- Advanced filtering and search
- Bulk operations
- Detailed usage analytics
- System-wide code management

**Navigation:**
```
Admin Panel → Invite Codes
```

### Manager Portal (`/manager/invite-codes/`)

**Features:**
- Team-focused invite code management
- Simplified interface for managers
- Role and task group assignment
- Usage tracking for team codes

**Navigation:**
```
Manager Console → Quick Actions → Invite Codes
```

## 🛠️ Management Operations

### 1. Creating Invite Codes

#### Via Web Interface

**Admin Portal:**
1. Navigate to `/admin/invite-codes/`
2. Click "Create New Invite Code"
3. Fill out the form:
   - **Role**: Select user role (Staff, Manager, Admin, Viewer)
   - **Task Group**: Choose primary task group
   - **Maximum Uses**: Set usage limit (1 = single use)
   - **Expiration**: Set expiration in days (optional)
   - **Notes**: Add internal notes
4. Click "Create Invite Code"

**Manager Portal:**
1. Navigate to `/manager/invite-codes/`
2. Click "Create New Invite Code"
3. Follow same form process as Admin Portal

#### Via API

```bash
POST /api/invite-codes/create/
Content-Type: application/json

{
    "role": "staff",
    "task_group": "cleaning",
    "max_uses": 5,
    "expires_days": "30",
    "notes": "API created code"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Invite code created: ABC12345",
    "data": {
        "id": 1,
        "code": "ABC12345",
        "role": "staff",
        "task_group": "cleaning",
        "max_uses": 5,
        "used_count": 0,
        "is_active": true,
        "is_usable": true,
        "expires_at": "2025-10-13T12:00:00Z",
        "created_at": "2025-09-13T12:00:00Z",
        "notes": "API created code"
    }
}
```

### 2. Managing Invite Codes

#### List View Features

**Filtering Options:**
- **Role Filter** - Filter by user role
- **Task Group Filter** - Filter by task group
- **Status Filter** - Filter by status (Active, Inactive, Expired, Usable)
- **Search** - Search by code, creator, or notes

**Display Information:**
- Code (with copy functionality)
- Role and Task Group
- Created By
- Status (with color coding)
- Usage (used/max uses)
- Expiration Date
- Created Date
- Action Buttons

#### Individual Code Management

**Available Actions:**
- **View Details** - Complete code information
- **Edit** - Modify code settings (unused codes only)
- **Revoke** - Deactivate code
- **Reactivate** - Reactivate revoked code
- **Delete** - Permanently delete code (unused codes only)

### 3. Code Status Management

#### Status Types

| Status | Description | Color | Actions Available |
|--------|-------------|-------|------------------|
| **Active** | Code is active and usable | Green | View, Edit, Revoke, Delete |
| **Inactive** | Code has been revoked | Red | View, Reactivate, Delete |
| **Expired** | Code has passed expiration date | Yellow | View, Reactivate, Delete |
| **Usable** | Code is active and not expired | Blue | View, Edit, Revoke, Delete |

#### Status Transitions

```
Created → Active → Revoked → Reactivated → Active
   ↓         ↓         ↓
  Delete   Expired   Delete
```

### 4. Usage Tracking

#### Usage Metrics

- **Used Count** - Number of times code has been used
- **Max Uses** - Maximum allowed uses (0 = unlimited)
- **Used By** - List of users who used the code
- **Last Used** - Timestamp of last usage
- **Usage Percentage** - Visual progress bar

#### Usage Rules

- **Single Use Codes** - Can only be used once (recommended for security)
- **Multi-Use Codes** - Can be used multiple times up to max_uses
- **Unlimited Codes** - Can be used unlimited times (max_uses = 0)
- **User Tracking** - Each usage is tracked per user

## 🔧 API Reference

### Endpoints

#### Create Invite Code
```http
POST /api/invite-codes/create/
Authorization: Bearer <token>
Content-Type: application/json

{
    "role": "staff|manager|admin|viewer",
    "task_group": "general|cleaning|maintenance|laundry|lawn_pool",
    "max_uses": 1-1000,
    "expires_days": 1-365,
    "notes": "string"
}
```

#### Revoke Invite Code
```http
POST /api/invite-codes/{code_id}/revoke/
Authorization: Bearer <token>
```

#### List Invite Codes (Web Interface)
```http
GET /admin/invite-codes/?role=staff&task_group=cleaning&status=active&search=ABC
GET /manager/invite-codes/?role=staff&task_group=cleaning&status=active&search=ABC
```

### Error Handling

#### Common Error Responses

**400 Bad Request:**
```json
{
    "error": "Invalid role",
    "details": "Role must be one of: staff, manager, admin, viewer"
}
```

**403 Forbidden:**
```json
{
    "error": "Access denied",
    "details": "You do not have permission to manage invite codes"
}
```

**404 Not Found:**
```json
{
    "error": "Invite code not found",
    "details": "The requested invite code does not exist"
}
```

**500 Internal Server Error:**
```json
{
    "error": "Internal server error",
    "details": "An unexpected error occurred"
}
```

## 📊 Monitoring and Analytics

### Key Metrics

1. **Total Codes Created** - Overall code creation count
2. **Active Codes** - Currently usable codes
3. **Usage Rate** - Percentage of codes being used
4. **Expiration Rate** - Codes expiring soon
5. **Role Distribution** - Codes by user role
6. **Task Group Distribution** - Codes by task group

### Audit Trail

All invite code operations are logged with:
- **User** - Who performed the action
- **Action** - What was done (create, edit, revoke, etc.)
- **Timestamp** - When the action occurred
- **Details** - Additional context information
- **IP Address** - Source of the action

## 🚀 Best Practices

### Security Recommendations

1. **Use Single-Use Codes** - Set max_uses to 1 for better security
2. **Set Expiration Dates** - Don't create permanent codes
3. **Regular Cleanup** - Remove unused expired codes
4. **Monitor Usage** - Track code usage patterns
5. **Limit Access** - Only give invite code management to trusted users

### Operational Guidelines

1. **Code Naming** - Use descriptive notes for code purpose
2. **Role Assignment** - Assign appropriate roles for user needs
3. **Task Group Mapping** - Match codes to actual work assignments
4. **Regular Review** - Periodically review and clean up codes
5. **Documentation** - Keep notes about code purposes

### Performance Optimization

1. **Pagination** - Large code lists are paginated (20 per page)
2. **Filtering** - Use filters to reduce data load
3. **Caching** - Frequently accessed data is cached
4. **Database Indexing** - Optimized queries for fast retrieval

## 🧪 Testing

### Test Coverage

The system includes comprehensive tests:

- **Unit Tests** - Individual component testing
- **Integration Tests** - End-to-end workflow testing
- **API Tests** - RESTful endpoint testing
- **Permission Tests** - Access control validation
- **Performance Tests** - Load and stress testing

### Running Tests

```bash
# Run all invite code tests
python manage.py test tests.unit.test_invite_code_management
python manage.py test tests.integration.test_invite_code_integration

# Run specific test categories
python manage.py test tests.unit.test_invite_code_management.InviteCodeManagementTestCase
python manage.py test tests.integration.test_invite_code_integration.InviteCodeIntegrationTestCase
```

### Test Data

Test fixtures include:
- Sample invite codes with various configurations
- Test users with different roles
- Expired and active codes
- Used and unused codes

## 🔄 Migration and Deployment

### Database Migrations

The system uses Django migrations for database schema changes:

```bash
# Create migration
python manage.py makemigrations api

# Apply migration
python manage.py migrate
```

### Deployment Checklist

- [ ] Run database migrations
- [ ] Update URL patterns
- [ ] Deploy templates
- [ ] Configure permissions
- [ ] Test all endpoints
- [ ] Verify access control
- [ ] Run test suite
- [ ] Monitor logs

## 📞 Support and Troubleshooting

### Common Issues

1. **Permission Denied** - Check user role and permissions
2. **Code Not Found** - Verify code ID and existence
3. **Validation Errors** - Check form data and API payload
4. **Performance Issues** - Check database indexes and query optimization

### Debug Mode

Enable debug logging for invite code operations:

```python
LOGGING = {
    'loggers': {
        'api.invite_code_views': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

### Contact Information

For technical support or questions about the invite code management system:

- **System Administrator** - admin@aristay.com
- **Development Team** - dev@aristay.com
- **Documentation** - docs@aristay.com

---

## 📝 Changelog

### Version 2.0 (2025-09-13)
- ✅ Added Manager Portal support
- ✅ Enhanced UI with responsive design
- ✅ Added comprehensive filtering and search
- ✅ Implemented usage tracking and analytics
- ✅ Added API endpoints for programmatic access
- ✅ Enhanced security with permission validation
- ✅ Added comprehensive test coverage
- ✅ Improved documentation and user guides

### Version 1.0 (2025-09-11)
- ✅ Initial implementation
- ✅ Basic Admin Portal functionality
- ✅ Core invite code management features
- ✅ Basic permission system
- ✅ Simple UI templates

---

**Last Updated:** September 13, 2025  
**Next Review:** October 13, 2025
