# AriStay Documentation

This directory contains comprehensive documentation for the AriStay property management application.

## 📁 Documentation Structure

### Backend Documentation (`backend/`)
- **[DYNAMIC_PERMISSIONS_ROBUST_IMPLEMENTATION.md](backend/DYNAMIC_PERMISSIONS_ROBUST_IMPLEMENTATION.md)** - Complete guide to the dynamic permission system
- **[DOCUMENTATION.md](backend/DOCUMENTATION.md)** - General backend documentation
- **[LOGGING.md](backend/LOGGING.md)** - Logging system documentation
- **[HISTORY_LOGGING_DOCUMENTATION.md](backend/HISTORY_LOGGING_DOCUMENTATION.md)** - History tracking system
- **[HISTORY_LOGGING_QUICK_REFERENCE.md](backend/HISTORY_LOGGING_QUICK_REFERENCE.md)** - Quick reference for history logging
- **[MOBILE_RESPONSIVENESS_DOCUMENTATION.md](backend/MOBILE_RESPONSIVENESS_DOCUMENTATION.md)** - Mobile responsiveness features
- **[STAFF_PORTAL_DOCUMENTATION.md](backend/STAFF_PORTAL_DOCUMENTATION.md)** - Staff portal documentation
- **[TIMEZONE_IMPLEMENTATION.md](backend/TIMEZONE_IMPLEMENTATION.md)** - Timezone handling implementation

### Feature Documentation (`features/`)
- **[BOOKING_ADMIN_ENHANCEMENTS.md](features/BOOKING_ADMIN_ENHANCEMENTS.md)** - Booking administration improvements
- **[CHARTS_FEATURE.md](features/CHARTS_FEATURE.md)** - Charts and analytics features
- **[CONFLICT_SYSTEM_EXPLAINED.md](features/CONFLICT_SYSTEM_EXPLAINED.md)** - Booking conflict resolution system
- **[DYNAMIC_DRF_PERMISSIONS.md](features/DYNAMIC_DRF_PERMISSIONS.md)** - Dynamic DRF permissions implementation
- **[ENHANCED_EXCEL_IMPORT_INTEGRATION.md](features/ENHANCED_EXCEL_IMPORT_INTEGRATION.md)** - Enhanced Excel import features
- **[EXCEL_IMPORT_FEATURE.md](features/EXCEL_IMPORT_FEATURE.md)** - Excel import functionality
- **[FILE_STORAGE_OPTIMIZATION.md](features/FILE_STORAGE_OPTIMIZATION.md)** - File storage optimization
- **[IMPROVEMENT_PLAN.md](features/IMPROVEMENT_PLAN.md)** - Future improvement plans
- **[PERMISSION_SYSTEM_IMPLEMENTATION.md](features/PERMISSION_SYSTEM_IMPLEMENTATION.md)** - Permission system implementation
- **[UI_UX_IMPROVEMENTS.md](features/UI_UX_IMPROVEMENTS.md)** - UI/UX improvements

### Fix Documentation (`fixes/`)
- **[COMPLETE_USER_ADMIN_FIX.md](fixes/COMPLETE_USER_ADMIN_FIX.md)** - Complete user admin fixes
- **[CONFLICT_RESOLUTION_FIXED.md](fixes/CONFLICT_RESOLUTION_FIXED.md)** - Conflict resolution fixes
- **[DASHBOARD_ROUTING_FIXES.md](fixes/DASHBOARD_ROUTING_FIXES.md)** - Dashboard routing fixes
- **[MANAGER_ADMIN_FIX.md](fixes/MANAGER_ADMIN_FIX.md)** - Manager admin interface fixes
- **[USER_ADMIN_FIX.md](fixes/USER_ADMIN_FIX.md)** - User admin interface fixes

### Requirements (`requirements/`)
- **[AriStay-App-Development-Requirements-Aug27.docx](requirements/AriStay-App-Development-Requirements-Aug27.docx)** - Initial requirements (Aug 27)
- **[AriStay-App-Development-Requirements-Aug29.docx](requirements/AriStay-App-Development-Requirements-Aug29.docx)** - Updated requirements (Aug 29)
- **[AriStay-App-Development.txt](requirements/AriStay-App-Development.txt)** - Text version of requirements
- **[Cleaning schedule.xlsx](requirements/Cleaning%20schedule.xlsx)** - Sample cleaning schedule

## 🚀 Quick Start

### For Developers
1. Start with **[PROJECT_README.md](PROJECT_README.md)** for project overview
2. Read **[backend/DYNAMIC_PERMISSIONS_ROBUST_IMPLEMENTATION.md](backend/DYNAMIC_PERMISSIONS_ROBUST_IMPLEMENTATION.md)** for permission system
3. Check **[backend/DOCUMENTATION.md](backend/DOCUMENTATION.md)** for backend details

### For System Administrators
1. Review **[backend/LOGGING.md](backend/LOGGING.md)** for logging configuration
2. Study **[backend/TIMEZONE_IMPLEMENTATION.md](backend/TIMEZONE_IMPLEMENTATION.md)** for timezone handling
3. Check **[fixes/](fixes/)** for known issues and solutions

### For Feature Development
1. Browse **[features/](features/)** for feature documentation
2. Check **[requirements/](requirements/)** for project requirements
3. Review **[fixes/](fixes/)** for common issues and solutions

## 🧪 Testing

### Permission System Testing
```bash
# Test permission system
python scripts/test_permissions.py

# Test API endpoints with permissions
python scripts/test_api_permissions.py

# Run comprehensive permission tests
python -m pytest tests/permissions/test_dynamic_permissions.py
```

### Setup Permissions
```bash
# Initialize permission system
python manage.py setup_permissions

# Reset permissions (use with caution)
python manage.py setup_permissions --reset
```

## 📚 Key Features

### 🔐 Dynamic Permission System
- **Role-based access control** (Superuser, Manager, Staff, Viewer)
- **User permission overrides** with expiration
- **Delegation system** for permission management
- **38 custom permissions** across all system areas
- **API endpoint protection** with proper HTTP status codes

### 📊 Booking Management
- **Excel import/export** functionality
- **Conflict resolution** system
- **Booking history** tracking
- **Multi-platform integration** (Airbnb, VRBO, etc.)

### 🏠 Property Management
- **Property inventory** tracking
- **Task management** with photos
- **Checklist templates** and automation
- **Device management** for smart properties

### 📱 Mobile Integration
- **Flutter frontend** with responsive design
- **Push notifications** via Firebase
- **Offline capability** for task management
- **Photo upload** and management

## 🔧 Development Tools

### Scripts
- **Permission management** scripts in `scripts/permissions/`
- **Testing utilities** in `scripts/`
- **Admin tools** in `scripts/admin/`

### Testing
- **Comprehensive test suite** in `tests/`
- **Permission tests** in `tests/permissions/`
- **API tests** in `tests/api/`
- **Booking tests** in `tests/booking/`

## 📞 Support

For questions or issues:
1. Check the relevant documentation in this directory
2. Review the **[fixes/](fixes/)** directory for known solutions
3. Check the test files for usage examples
4. Run the test scripts to verify system functionality

---

**Last Updated**: September 1, 2025  
**Version**: 1.0  
**Status**: ✅ Production Ready
