# 👥 User Workflows & Access Guide

## 🔐 **User Types & Access Patterns**

### **1. SUPERUSER (System Administrator)**

**Role**: Full system administration and oversight  
**Username**: `admin_super` | **Password**: `admin123`

#### **🌐 Interface Access**:
- **Django Admin Portal**: `http://localhost:8000/admin/`
- **Manager Interface**: `http://localhost:8000/manager/` (full access)
- **Staff Portal**: `http://localhost:8000/api/staff/` (read-only oversight)
- **API Endpoints**: All endpoints with full CRUD permissions

#### **📋 Capabilities**:
- ✅ User management (create/edit/delete users)
- ✅ Property management (all properties)
- ✅ Booking management (import, edit, delete)
- ✅ Task management (create, assign, modify, delete)
- ✅ System configuration (settings, permissions)
- ✅ Audit logs and system monitoring
- ✅ Database migrations and maintenance
- ✅ Excel import with conflict resolution
- ✅ Permission management
- ✅ System-wide notifications

#### **🔑 Typical Workflow**:
1. **Access Django Admin** → Manage users, permissions, system settings
2. **Use Manager Interface** → Oversee all properties and operations
3. **Review Staff Portal** → Monitor task completion and staff performance
4. **API Access** → Integrate with external systems or mobile apps
5. **Import Data** → Process Excel booking imports with conflict resolution
6. **System Maintenance** → Update settings, run maintenance commands

---

### **2. MANAGER (Property Manager)**

**Role**: Property oversight and staff management  
**Username**: `manager_alice` | **Password**: `manager123`

#### **🌐 Interface Access**:
- **Manager Interface**: `http://localhost:8000/manager/` (primary interface)
- **Django Admin Portal**: `http://localhost:8000/admin/` (limited access)
- **API Endpoints**: Property and task management APIs

#### **📋 Capabilities**:
- ✅ Property management (assigned properties only)
- ✅ Booking management (view, edit, import for owned properties)
- ✅ Task creation and assignment
- ✅ Staff performance monitoring
- ✅ Excel booking imports
- ✅ Inventory management
- ✅ Guest communication
- ✅ Property maintenance scheduling
- ❌ User creation/deletion (except staff assignment)
- ❌ System settings modification
- ❌ Cross-property access (without ownership)

#### **🔑 Typical Workflow**:
1. **Login to Manager Interface** → Daily dashboard overview
2. **Review Bookings** → Check upcoming arrivals/departures
3. **Create Tasks** → Assign cleaning, maintenance, setup tasks to staff
4. **Monitor Progress** → Track task completion and staff performance  
5. **Import Bookings** → Process Excel files from booking platforms
6. **Handle Conflicts** → Resolve booking conflicts during import
7. **Manage Inventory** → Track supplies and maintenance items
8. **Generate Reports** → Property performance and task completion

---

### **3. STAFF/CREW (Task Executor)**

**Role**: Task execution and property maintenance  
**Usernames**: `staff_bob`, `crew_charlie`, `crew_diana`, `crew_eve`  
**Password**: `staff123` or `crew123`

#### **🌐 Interface Access**:
- **Staff Portal**: `http://localhost:8000/api/staff/` (primary interface)
- **Mobile App**: Flutter app for field work
- **API Endpoints**: Task and notification APIs (limited)

#### **📋 Capabilities**:
- ✅ View assigned tasks
- ✅ Update task status and notes
- ✅ Upload task completion photos
- ✅ Receive notifications
- ✅ View property details (assigned tasks only)
- ✅ Check inventory levels
- ✅ Report issues or maintenance needs
- ❌ Create new tasks
- ❌ Assign tasks to others
- ❌ Access other users' tasks
- ❌ Modify bookings
- ❌ System administration

#### **🔑 Typical Workflow**:
1. **Login to Staff Portal** → Check assigned tasks for the day
2. **Review Task Details** → Understand requirements, deadlines, locations
3. **Navigate to Property** → Use address and property details
4. **Execute Tasks** → Complete cleaning, maintenance, setup work
5. **Update Status** → Mark tasks as in-progress, then completed
6. **Add Notes/Photos** → Document work completion and issues
7. **Report Problems** → Notify manager of maintenance needs
8. **Check Notifications** → Stay updated on new assignments

---

## 🛠️ **Interface-Specific Features**

### **Django Admin Portal** (`/admin/`)
- **Who**: Superuser, Manager (limited)
- **Purpose**: System administration and data management
- **Key Features**:
  - User management interface
  - Bulk data operations
  - Model-level CRUD operations
  - System settings configuration
  - Advanced filtering and search

### **Manager Interface** (`/manager/`)
- **Who**: Superuser, Manager
- **Purpose**: Property and staff management
- **Key Features**:
  - Dashboard with key metrics
  - Property portfolio overview
  - Task management and assignment
  - Booking import and conflict resolution
  - Staff performance tracking
  - Inventory management

### **Staff Portal** (`/api/staff/`)
- **Who**: All users (role-based content)
- **Purpose**: Task execution and field work
- **Key Features**:
  - Personal task list
  - Task status updates
  - Photo upload capability
  - Notification center
  - Property information lookup

### **API Endpoints** (`/api/`)
- **Who**: All users (permission-based)
- **Purpose**: Programmatic access and mobile app backend
- **Key Features**:
  - RESTful API with JWT authentication
  - Role-based permissions
  - Mobile app integration
  - Third-party system integration

---

## 📱 **Mobile App Integration**

### **Flutter Frontend**: 
- **Purpose**: Field work and mobile task management
- **Target Users**: Primarily staff/crew, secondary manager oversight
- **Key Features**:
  - Offline task access
  - Photo capture and upload
  - GPS-based property navigation
  - Push notifications
  - Barcode scanning for inventory

---

## 🔐 **Permission Matrix**

| Feature | Superuser | Manager | Staff |
|---------|-----------|---------|-------|
| Create Users | ✅ | ❌ | ❌ |
| Manage Properties | ✅ | ✅ (owned) | ❌ |
| Import Bookings | ✅ | ✅ | ❌ |
| Create Tasks | ✅ | ✅ | ❌ |
| Execute Tasks | ✅ | ✅ | ✅ |
| System Settings | ✅ | ❌ | ❌ |
| View All Data | ✅ | ❌ | ❌ |
| API Access | ✅ | ✅ (limited) | ✅ (limited) |

---

## 🚀 **Getting Started - Testing Scenarios**

### **Scenario 1: New Booking Import** (Manager Workflow)
1. Login as `manager_alice`
2. Go to Manager Interface → Bookings → Import
3. Upload sample Excel file
4. Resolve any conflicts
5. Verify tasks auto-created

### **Scenario 2: Task Assignment & Execution** (Manager + Staff)
1. **Manager**: Create cleaning task for upcoming booking
2. **Manager**: Assign to `staff_bob`
3. **Staff**: Login to Staff Portal
4. **Staff**: Accept and complete task
5. **Manager**: Review completion

### **Scenario 3: System Administration** (Superuser Workflow)
1. Login as `admin_super`
2. Review all system activity in Django Admin
3. Monitor staff performance across all properties
4. Update system configurations
5. Generate system-wide reports

Run the test data script to populate these scenarios with realistic data!
