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

| Role | Access Level | Responsibilities |
|------|-------------|------------------|
| **Superuser** | Full system access | System configuration, user management, all data |
| **Manager** | Property management | Staff coordination, task oversight, reporting |
| **Cleaning Staff** | Assigned cleaning tasks | Room cleaning, checklists, photo uploads |
| **Maintenance Staff** | Maintenance + inventory | Repairs, inspections, inventory management |
| **Laundry Staff** | Laundry workflow | Linen handling, washing, restocking |
| **Lawn/Pool** | Outdoor maintenance | Landscaping, pool care, equipment |
| **Viewer** | Read-only access | Property owners, external stakeholders |

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

### 2. 📦 Inventory Management

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

### 3. 👥 Workflow Specialization

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

### 4. 🔄 Recurring Schedules

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

### 5. 🗂️ Lost & Found System

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

### 6. 📅 Booking Calendar Import

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
- **Dual admin sites**: Superuser (`/admin/`) and Manager (`/manager/`)
- **Permission boundaries**: Role-based access control
- **Inline editing**: Related model management
- **Visual indicators**: Color-coded status displays

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
- **Superuser**: Full system access, all models
- **Manager**: Property management, staff oversight
- **Staff roles**: Task-specific access only
- **Viewer**: Read-only property viewing

### Data Protection
- **Field-level security**: Hide sensitive data (passwords)
- **Audit logging**: Track all changes with user attribution
- **Permission boundaries**: Enforce role restrictions
- **Session management**: Secure authentication

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

This documentation covers the complete MVP Phase 1 implementation. All features are production-ready and include comprehensive admin interfaces for ongoing management.
