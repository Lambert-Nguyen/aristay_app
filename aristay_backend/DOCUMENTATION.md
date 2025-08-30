# AriStay MVP Phase 1 - Complete Documentation

## 📋 Overview

AriStay is a comprehensive property management system designed for cleaning, maintenance, inventory, and staff coordination. This documentation covers the MVP Phase 1 implementation, which provides the foundation for property-centric task management with specialized workflows.

## 🏗️ System Architecture

### Core Concepts
- **Property-Centric**: Everything revolves around properties
- **Booking-Driven**: Tasks are linked to guest bookings when applicable  
- **Role-Based**: Different user roles have specialized workflows
- **Checklist-Driven**: Tasks use structured checklists for consistency
- **Automated**: Recurring schedules generate tasks automatically

### User Roles

| Role | Access Level | Responsibilities | Password Management |
|------|-------------|------------------|-------------------|
| **Superuser** | Full system access | System configuration, user management, all data | ✅ Direct password changes + email reset |
| **Manager** | Property management | Staff coordination, task oversight, reporting | ❌ Email reset only (no direct changes) |
| **Cleaning Staff** | Assigned cleaning tasks | Room cleaning, checklists, photo uploads | ❌ Email reset only |
| **Maintenance Staff** | Maintenance + inventory | Repairs, inspections, inventory management | ❌ Email reset only |
| **Laundry Staff** | Laundry workflow | Linen handling, washing, restocking | ❌ Email reset only |
| **Lawn/Pool** | Outdoor maintenance | Landscaping, pool care, equipment | ❌ Email reset only |
| **Viewer** | Read-only access | Property owners, external stakeholders | ❌ No password management access |

## 🎯 MVP Phase 1 Features

### 1. ✅ Checklists System

**Purpose**: Standardized, room-by-room task completion with proof requirements.

#### Models
- `ChecklistTemplate`: Reusable checklist designs for task types
- `ChecklistItem`: Individual steps within a checklist
- `TaskChecklist`: Checklist instance attached to a specific task
- `ChecklistResponse`: Staff responses to checklist items
- `ChecklistPhoto`: Photo evidence attached to responses

#### Key Features
- **Room-specific items**: Bathroom, bedroom, kitchen, living room sections
- **Item types**: 
  - `check`: Simple checkbox
  - `photo_required`: Must upload photo to complete
  - `photo_optional`: Optional photo
  - `text_input`: Text response required
  - `number_input`: Numeric input (e.g., linen count)
  - `blocking`: Must complete before task can progress
- **Completion tracking**: Automatic progress calculation
- **Photo evidence**: Visual proof of work completion

#### Usage
```python
# Create a checklist template
template = ChecklistTemplate.objects.create(
    name="Standard Room Cleaning",
    task_type="cleaning",
    created_by=admin_user
)

# Add checklist items
ChecklistItem.objects.create(
    template=template,
    title="Clean and disinfect toilet",
    room_type="bathroom",
    item_type="blocking",
    order=1
)
```

#### Admin Interface
- **Superuser**: `/admin/api/checklisttemplate/` - Full template management
- **Manager**: `/manager/api/checklisttemplate/` - Template oversight
- Templates automatically create task checklists when tasks are assigned

### 7. 🔐 Password Reset & User Management System

**Purpose**: Secure, role-based password management with granular permissions and user-friendly reset workflows.

#### Security Features
- **Role-Based Access Control**: Different password management capabilities per user role
- **Secure Email Reset**: Token-based password reset with expiration
- **Permission Boundaries**: Managers cannot directly change passwords (email reset only)
- **Audit Logging**: All password changes and reset requests are logged

#### Password Management by Role

**Superuser Admin (`/admin/`)**:
- ✅ **Direct Password Changes**: Can set/modify passwords directly in admin interface
- ✅ **Email Password Reset**: Can trigger password reset emails for any user
- ✅ **Bulk Reset Actions**: "Send password reset email" for multiple users
- ✅ **Individual Reset Button**: "🔄 Send Password Reset Email" on each user form
- ✅ **Full User Management**: Complete CRUD operations on all users

**Manager Admin (`/manager/`)**:
- ❌ **No Direct Password Changes**: Cannot modify passwords directly
- ✅ **Email Password Reset Only**: Can trigger password reset emails
- ✅ **Bulk Reset Actions**: "Send password reset email" for managed users
- ✅ **Individual Reset Button**: "🔄 Send Password Reset Email" on each user form
- ✅ **Limited User Management**: Can modify groups, roles, but not sensitive fields

**Staff/Portal Users**:
- ✅ **Self-Service Reset**: Can request password reset via email
- ✅ **Secure Token Process**: Time-limited reset links
- ❌ **No Admin Access**: Cannot manage other users' passwords

#### Implementation Details

**Custom Admin Classes**:
```python
class AriStayUserAdmin(DjangoUserAdmin):
    """Superuser admin with full password management capabilities"""

class UserManagerAdmin(DjangoUserAdmin):
    """Manager admin with restricted password management"""
```

**URL Patterns**:
```python
# Superuser admin
path('<id>/password/', user_change_password),  # Direct password changes
path('<id>/password-reset/', password_reset_view),  # Email reset

# Manager admin
path('<id>/password/', blocked_password_change),  # Blocks direct changes
path('<id>/password-reset/', password_reset_view),  # Email reset only
```

**Custom Templates**:
- `api/templates/admin/auth/user/change_form.html` - Superuser with reset button
- `api/templates/manager_admin/auth/user/change_form.html` - Manager with reset button
- `api/templates/admin/auth/user/change_password.html` - Custom password change form

#### Usage Examples

**Superuser Direct Password Change**:
```python
# In admin interface at /admin/auth/user/123/change/
# Superuser can directly set new password via form
```

**Manager Email Reset**:
```python
# In admin interface at /manager/auth/user/123/change/
# Manager can only trigger email reset
# User receives secure reset link
```

**User Self-Reset**:
```python
# Via Django's standard password reset flow
# POST to /api/auth/password_reset/
# User receives email with reset link
```

#### Security Considerations
- **Password Hashing**: All passwords stored as secure hashes
- **Token Expiration**: Reset links expire after configurable time
- **Rate Limiting**: Protection against brute force attacks
- **Audit Trail**: All password operations logged with user attribution
- **Permission Checks**: Role-based restrictions enforced at multiple levels

#### Admin Interface Features
- **Visual Indicators**: Clear buttons and form fields based on permissions
- **Error Handling**: Graceful failure with informative messages
- **Bulk Operations**: Mass password reset for multiple users
- **Permission Feedback**: Clear messaging when actions are restricted

This password management system provides enterprise-grade security while maintaining usability across different user roles and administrative levels.

### 8. 📦 Inventory Management

**Purpose**: Complete supply tracking with automatic alerts and usage monitoring.

#### Models
- `InventoryCategory`: Supply categories (Cleaning, Bathroom, Kitchen, etc.)
- `InventoryItem`: Master catalog of trackable items
- `PropertyInventory`: Stock levels per property per item
- `InventoryTransaction`: All stock movements and updates

#### Key Features
- **Property-specific tracking**: Each property maintains its own inventory
- **Par level management**: Minimum stock thresholds with alerts
- **Stock status indicators**:
  - `normal`: Above par level
  - `low_stock`: At or below par level
  - `out_of_stock`: Zero quantity
  - `overstocked`: Above maximum level
- **Transaction logging**: Full audit trail of all movements
- **Cost tracking**: Estimated costs per item for budgeting

#### Usage
```python
# Check inventory status
property_inventory = PropertyInventory.objects.filter(
    property_ref=property,
    current_stock__lte=models.F('par_level')
)  # Returns low-stock items

# Log a transaction
InventoryTransaction.objects.create(
    property_inventory=property_inventory,
    transaction_type='stock_out',
    quantity=5,
    task=maintenance_task,
    created_by=staff_user
)
```

#### Admin Interface
- **Color-coded status**: Visual indicators for stock levels
- **Transaction history**: Complete movement tracking
- **Alerts**: Automatic low-stock identification

### 9. 👥 Workflow Specialization

**Purpose**: Task-specific workflows optimized for different staff roles.

#### Pre-built Templates

**Cleaning Workflow**:
- Room-by-room checklists (bathroom, bedroom, kitchen, living room)
- Before/after photo requirements
- Damage reporting integration
- Supply usage tracking

**Maintenance Workflow**:
- HVAC system checks
- Plumbing and electrical inspections  
- Inventory level updates
- Repair documentation

**Laundry Workflow**:
- Pick-up linen counting
- Quality inspection
- Wash/dry completion
- Delivery and restocking

#### Implementation
- Task types automatically assign appropriate checklist templates
- Role-based task visibility in admin interfaces
- Specialized reporting per workflow type

### 10. 🔄 Recurring Schedules

**Purpose**: Automated task generation based on configurable schedules.

#### Models
- `ScheduleTemplate`: Recurring task definitions
- `GeneratedTask`: Tracking of auto-created tasks

#### Schedule Types
- **Daily**: Every X days
- **Weekly**: Specific weekdays
- **Monthly**: Specific day of month
- **Quarterly**: Every 3 months
- **Yearly**: Annual tasks

#### Features
- **Advance scheduling**: Create tasks X days before due date
- **Template integration**: Auto-assign checklists to generated tasks
- **Property-specific or global**: Flexible scope configuration
- **Smart scheduling**: Handles edge cases (Feb 31 → Feb 28)

#### Usage
```bash
# Generate tasks (run daily via cron)
python manage.py generate_scheduled_tasks

# Create sample schedules
python manage.py create_sample_schedules

# Dry run to preview
python manage.py generate_scheduled_tasks --dry-run
```

#### Management Command Setup
```bash
# Add to crontab for daily execution
0 6 * * * cd /path/to/aristay_backend && python manage.py generate_scheduled_tasks
```

### 11. 🗂️ Lost & Found System

**Purpose**: Track guest items found during cleaning with full lifecycle management.

#### Models
- `LostFoundItem`: Found item details and tracking
- `LostFoundPhoto`: Visual documentation

#### Workflow
1. **Found**: Staff logs item with photo and location
2. **Claimed**: Guest or authorized person retrieval
3. **Disposed/Donated**: Final disposition after retention period

#### Features
- **Property association**: Link to specific properties and bookings
- **Value estimation**: For insurance and tracking
- **Storage tracking**: Current location management
- **Photo documentation**: Visual evidence and identification

### 12. 📅 Booking Calendar Import

**Purpose**: External calendar integration with automatic task generation.

#### Models
- `BookingImportTemplate`: Import configuration per property
- `BookingImportLog`: Import history and error tracking

#### Supported Sources
- **CSV files**: Configurable field mapping
- **iCal/Calendar**: Standard calendar format
- **Airbnb Export**: Platform-specific format
- **VRBO Export**: Platform-specific format
- **API Integration**: Future custom integrations

#### Features
- **Field mapping**: Flexible CSV column configuration
- **Auto-task creation**: Generate cleaning tasks for check-ins
- **Error logging**: Track import failures for debugging
- **Multi-property support**: Different templates per property

## 🛠️ Technical Implementation

### Database Structure
- **PostgreSQL ready**: Designed for production scale
- **Foreign key relationships**: Proper data integrity
- **Timezone aware**: UTC storage with user-specific display
- **Audit trails**: Created/modified tracking throughout

### Admin Integration
- **Dual admin sites**: Superuser (`/admin/`) and Manager (`/manager/`) with custom namespaces
- **Password management**: Role-based password reset and change capabilities
- **Permission boundaries**: Strict role-based access control with granular permissions
- **Custom admin classes**: `AriStayUserAdmin` and `UserManagerAdmin` with specialized features
- **URL pattern fixes**: Resolved namespace conflicts and NoReverseMatch errors
- **Inline editing**: Related model management with security restrictions
- **Visual indicators**: Color-coded status displays and permission-aware UI elements

### API Integration
- **Django REST Framework**: Full CRUD operations
- **Token authentication**: Secure mobile app integration
- **Session authentication**: Web portal support
- **Filtering**: Advanced search and filter capabilities

## 📋 Management Commands

### Data Creation
```bash
# Create sample MVP data (run once)
python manage.py create_sample_mvp_data

# Create sample tasks with workflows
python manage.py create_sample_tasks

# Create recurring schedule templates
python manage.py create_sample_schedules
```

### Task Generation
```bash
# Generate scheduled tasks (daily cron)
python manage.py generate_scheduled_tasks

# Preview without creating
python manage.py generate_scheduled_tasks --dry-run

# Generate for specific date
python manage.py generate_scheduled_tasks --check-date 2025-01-15

# Generate for specific schedule only
python manage.py generate_scheduled_tasks --schedule-id 5
```

## 🔧 Configuration

### Required Settings
```python
# settings.py
TIME_ZONE = "America/New_York"  # Default system timezone
USE_TZ = True  # Enable timezone support

# Install python-dateutil for recurring schedules
pip install python-dateutil==2.9.0.post0
```

### Database Migrations
```bash
# Apply all MVP Phase 1 migrations
python manage.py migrate

# Specific migrations applied:
# - 0021_mvp_phase1_models: Core MVP models
# - 0022_fix_inventory_sku: SKU field constraint fix  
# - 0023_recurring_schedules_and_booking_import: Schedule system
```

## 📊 Reporting & Analytics

### Built-in Reports
- **Inventory Status**: Real-time stock levels across properties
- **Task Completion**: Progress tracking per workflow type
- **Schedule Performance**: Generated vs completed task ratios
- **Lost & Found**: Item lifecycle and recovery rates

### Admin Dashboards
- **Visual stock indicators**: Color-coded inventory status
- **Completion percentages**: Checklist progress tracking
- **Schedule monitoring**: Last generation timestamps
- **Transaction histories**: Complete audit trails

## 🔒 Security & Permissions

### Role-Based Access
- **Superuser**: Full system access, all models, direct password management
- **Manager**: Property management, staff oversight, email password reset only
- **Staff roles**: Task-specific access only, self-service password reset
- **Viewer**: Read-only property viewing, no password management access

### Password Security
- **Granular Permissions**: Superusers can change passwords directly, managers can only send reset emails
- **Secure Email Reset**: Token-based password reset with configurable expiration
- **Audit Logging**: All password operations tracked with user attribution
- **Permission Enforcement**: Multiple layers of security checks

### Data Protection
- **Field-level security**: Hide sensitive data (passwords, hashed fields)
- **Role-based form restrictions**: Managers cannot modify username or password fields
- **Custom admin templates**: Secure password change forms with proper validation
- **Audit logging**: Track all changes with user attribution
- **Permission boundaries**: Enforce role restrictions at model, view, and template levels
- **Session management**: Secure authentication with proper timeout handling

## 🚀 Production Deployment

### Requirements
- Python 3.13+
- Django 5.1.7
- PostgreSQL (recommended)
- Redis (for caching, optional)

### Cron Jobs
```bash
# Daily task generation at 6 AM
0 6 * * * cd /path/to/aristay_backend && python manage.py generate_scheduled_tasks

# Weekly inventory reporting (optional)
0 8 * * 1 cd /path/to/aristay_backend && python manage.py send_inventory_report
```

### Monitoring
- Sentry integration for error tracking
- Structured JSON logging
- Performance monitoring with psutil
- Health check endpoints

## 🔜 Phase 2 Roadmap

### Planned Features
1. **In-App/Website Chat**: Real-time communication
2. **CSV Import/Export**: Advanced reporting
3. **Calendar View**: Unified scheduling interface
4. **Advanced Reports**: SLA compliance, property readiness
5. **AI Photo QA**: Automated quality assurance
6. **GPS Integration**: Location-based task verification

### Technical Enhancements
- **Real-time updates**: WebSocket integration
- **Mobile optimization**: Progressive Web App
- **Advanced filtering**: Dynamic report generation
- **Integration APIs**: Third-party service connections

---

## 📞 Support

For implementation questions or technical support:
- Check admin interfaces at `/admin/` (Superuser) or `/manager/` (Manager)
- Review management command help: `python manage.py help <command>`
- Examine sample data for usage patterns
- Monitor application logs for operational insights

## 📊 System Metrics Dashboard

### Overview
Comprehensive system monitoring and performance insights for superusers to maintain optimal application health.

### Access
- **URL**: `/api/admin/metrics/`
- **Permissions**: Superuser only
- **Auto-refresh**: Every 30 seconds
- **API Endpoint**: `/api/admin/metrics/api/` (JSON)

### Metrics Categories

#### 🖥️ Performance Metrics
- **CPU Usage**: Real-time processor utilization
- **Memory Usage**: RAM consumption and availability
- **Disk Usage**: Storage space and free capacity
- **Network Statistics**: Data transfer metrics

#### 💾 Database Metrics
- **Connection Status**: Database connectivity health
- **Table Counts**: Record counts across all models
- **Recent Activity**: Today's data creation statistics

#### 📝 Logging Metrics
- **Log Files**: Size and line counts for all log files
- **Log Directory**: Location and write permissions
- **Logging Status**: System logging configuration health

#### 🏥 Health Checks
- **Overall Status**: System health (Healthy/Warning/Critical)
- **Individual Checks**: Database, cache, disk, memory, logging
- **Failed Components**: Automatic detection of issues

#### 👥 Application Metrics
- **Task Statistics**: Total, pending, completed, overdue tasks
- **User Activity**: Login patterns, role distribution
- **Property Data**: Active properties and bookings
- **Notification Activity**: Sent and unread notifications

#### ⚙️ System Information
- **Environment**: Python version, platform, hostname
- **Configuration**: Debug mode, timezone settings
- **Process Info**: PID, uptime, memory usage

### Features
- **Real-time Updates**: Automatic refresh without page reload
- **Health Monitoring**: Visual status indicators for system components
- **Performance Alerts**: Color-coded warnings for resource usage
- **Mobile Responsive**: Works on all device sizes
- **Error Handling**: Graceful failure with retry options

### Usage in Admin Dashboard
1. Login as superuser
2. Navigate to admin dashboard
3. Click "🖥️ System Metrics" card
4. View comprehensive system status
5. Monitor performance in real-time

This system metrics dashboard provides essential monitoring capabilities for maintaining optimal system performance and early detection of potential issues.

---

## 🆕 Recent Updates & Bug Fixes

### Version: MVP Phase 1 - Enhanced (Latest)

#### 🔧 Critical Bug Fixes (Latest)

**1. Password Reset System Overhaul**
- ✅ **Custom Admin Templates**: Fixed `NoReverseMatch: 'app_list'` errors with custom password change forms
- ✅ **URL Namespace Resolution**: Corrected manager admin namespace from `manager` to `manager_admin`
- ✅ **Permission Boundaries**: Enhanced role-based password management restrictions
- ✅ **Template Compatibility**: Created Django-compatible password change templates

**2. Admin Site URL Pattern Fixes**
- ✅ **Namespace Conflicts**: Resolved `NoReverseMatch` errors in admin URL patterns
- ✅ **Custom Admin Classes**: Implemented `AriStayUserAdmin` and `UserManagerAdmin` with proper inheritance
- ✅ **URL Pattern Consistency**: Standardized URL patterns across superuser and manager admin sites
- ✅ **Template Context**: Fixed template context issues with password reset buttons

**3. Enhanced Security Features**
- ✅ **Password Change Restrictions**: Managers cannot directly modify passwords (email reset only)
- ✅ **Form Field Validation**: Role-based form field restrictions and validations
- ✅ **Audit Trail Enhancement**: Improved logging of password operations
- ✅ **Session Security**: Enhanced session management and timeout handling

#### 🎨 UI/UX Improvements

**Admin Interface Enhancements**:
- ✅ **Password Reset Buttons**: Added "🔄 Send Password Reset Email" buttons to both admin interfaces
- ✅ **Bulk Actions**: "Send password reset email to selected users" functionality
- ✅ **Visual Indicators**: Clear permission-based UI elements and form restrictions
- ✅ **Error Handling**: Improved error messages and user feedback

**Template System Updates**:
- ✅ **Custom Change Forms**: `api/templates/admin/auth/user/change_form.html`
- ✅ **Manager Templates**: `api/templates/manager_admin/auth/user/change_form.html`
- ✅ **Password Change Forms**: `api/templates/admin/auth/user/change_password.html`
- ✅ **Breadcrumb Navigation**: Fixed navigation issues in custom templates

#### 🛠️ Technical Implementation Details

**URL Configuration**:
```python
# Fixed manager admin namespace
path('manager/', include((manager_site.urls[0], 'admin'), namespace='manager_admin')),

# Custom admin URL patterns
path('<id>/password/', user_change_password),  # Superuser: direct changes
path('<id>/password/', blocked_password_change),  # Manager: blocked
path('<id>/password-reset/', password_reset_view),  # Both: email reset
```

**Permission Logic**:
```python
# Superuser: Full password management
if request.user.is_superuser:
    # Can change passwords directly
    # Can send password reset emails

# Manager: Restricted password management
else:
    # Cannot change passwords directly
    # Can only send password reset emails
    # Form fields restricted (username, password hidden)
```

**Template Security**:
```html
<!-- Superuser admin template -->
{% if password_reset_url %}
<a href="{{ password_reset_url }}" class="btn btn-primary">
    🔄 Send Password Reset Email
</a>
{% endif %}

<!-- Manager admin template -->
{% if password_reset_url %}
<a href="{{ password_reset_url }}" class="btn btn-primary">
    🔄 Send Password Reset Email
</a>
{% endif %}
```

#### 📊 System Health Verification

**Post-Fix Status**:
- ✅ **Django System Check**: `python manage.py check` - No issues
- ✅ **URL Pattern Tests**: All URL reversals working correctly
- ✅ **Template Rendering**: Custom templates loading without errors
- ✅ **Permission Enforcement**: Role-based restrictions functioning
- ✅ **Error Logs**: Cleared and ready for fresh monitoring

**Testing Results**:
```bash
✅ Admin changelist: /admin/auth/user/
✅ Admin change: /admin/auth/user/1/change/
✅ Admin password reset: /admin/auth/user/1/password-reset/
✅ Manager changelist: /manager/auth/user/
✅ Manager change: /manager/auth/user/1/change/
✅ Manager password reset: /manager/auth/user/1/password-reset/
```

---

## 📋 Change Log

### Version History
- **MVP Phase 1 - Initial Release**: Core property management system
- **MVP Phase 1 - Enhanced**: Password reset system, admin fixes, security improvements
- **Latest Update**: Namespace fixes, template compatibility, comprehensive documentation

### Migration Status
- ✅ **All migrations applied**: Database schema up-to-date
- ✅ **Management commands**: All working correctly
- ✅ **Dependencies**: All requirements satisfied
- ✅ **Environment**: Production-ready configuration

---

This documentation covers the complete MVP Phase 1 implementation including all recent bug fixes and security enhancements. The system is now production-ready with enterprise-grade password management and comprehensive admin interfaces.
