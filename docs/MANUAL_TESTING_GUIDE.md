# 🧪 Manual Testing Guide

## 🚀 **Quick Start**

**Setup & Run Test Data:**
```bash
cd aristay_backend
python manage.py create_test_data
python manage.py runserver
```

**Access URLs:**
- **Django Admin**: http://localhost:8000/admin/
- **Manager Interface**: http://localhost:8000/manager/
- **Staff Portal**: http://localhost:8000/api/staff/
- **API Root**: http://localhost:8000/api/

---

## 👥 **Test User Accounts**

| Role | Username | Password | Description |
|------|----------|----------|-------------|
| **Superuser** | `admin_super` | `admin123` | Full system admin access |
| **Manager** | `manager_alice` | `manager123` | Property management |
| **Staff** | `staff_bob` | `staff123` | Task execution (cleaning) |
| **Crew** | `crew_charlie` | `crew123` | Maintenance specialist |
| **Crew** | `crew_diana` | `crew123` | Laundry specialist |
| **Crew** | `crew_eve` | `crew123` | Pool maintenance |

---

## 🏗️ **Test Data Overview**

### **Properties Created:**
1. **Sunset Villa** - 123 Beach Front Dr, Santa Monica, CA 90401
2. **Downtown Loft** - 456 Urban St, Los Angeles, CA 90015  
3. **Mountain Cabin** - 789 Pine Tree Rd, Big Bear, CA 92315
4. **City Condo** - 321 High Rise Ave, San Francisco, CA 94105

### **Bookings Created:**
- **John & Sarah Smith** → Sunset Villa (2 days from now, 3-day stay)
- **Maria Garcia** → Downtown Loft (tomorrow, 2-day stay)
- **The Johnson Family** → Mountain Cabin (1 week from now, 3-day stay)
- **David Wilson** → Sunset Villa (completed stay, 2 days ago)

### **Tasks Created:**
- **Pre-arrival Cleaning** - Sunset Villa (assigned to staff_bob)
- **Post-checkout Cleaning** - Sunset Villa (in-progress, staff_bob)
- **Pre-arrival Setup** - Downtown Loft (assigned to crew_diana)
- **HVAC Maintenance** - Mountain Cabin (assigned to crew_charlie)
- **Routine Inspection** - City Condo (completed by crew_charlie)
- **Pool Maintenance** - Sunset Villa (assigned to crew_eve)

---

## 🧪 **Testing Scenarios**

### **Scenario 1: Superuser Full Access**
1. **Login**: `admin_super` / `admin123` → http://localhost:8000/admin/
2. **Test User Management**:
   - Navigate to Users → View all 6 test users
   - Edit any user profile and permissions
   - Create new user and assign role
3. **Test System Oversight**:
   - View all properties across all managers
   - Access all bookings and tasks
   - Review audit logs and system activity

### **Scenario 2: Manager Workflow**
1. **Login**: `manager_alice` / `manager123` → http://localhost:8000/manager/
2. **Test Property Management**:
   - View dashboard with 4 properties
   - Check upcoming bookings (John & Sarah, Maria, Johnson Family)
   - Review completed booking (David Wilson)
3. **Test Task Management**:
   - View all 6 assigned tasks
   - Create new cleaning task for upcoming booking
   - Assign task to available crew member
   - Monitor task completion status
4. **Test Booking Import** (if available):
   - Access booking import interface
   - Test Excel import functionality
   - Handle conflict resolution

### **Scenario 3: Staff Task Execution**
1. **Login**: `staff_bob` / `staff123` → http://localhost:8000/api/staff/
2. **Test Task View**:
   - View assigned tasks: Pre-arrival cleaning, Post-checkout cleaning
   - Check task details: property address, requirements, deadlines
3. **Test Task Updates**:
   - Change task status from 'pending' to 'in-progress'
   - Add completion notes
   - Mark task as completed
4. **Test Notifications**:
   - View notification for new task assignment
   - Check read/unread status

### **Scenario 4: Crew Specialization**
1. **Login**: `crew_charlie` / `crew123`
2. **Test Maintenance Tasks**:
   - View HVAC maintenance task (Mountain Cabin)
   - View completed routine inspection (City Condo)
   - Update task status and add technical notes

### **Scenario 5: API Testing**
1. **Get JWT Token**:
   ```bash
   curl -X POST http://localhost:8000/api/token/ \
        -H "Content-Type: application/json" \
        -d '{"username": "manager_alice", "password": "manager123"}'
   ```

2. **Test Task Endpoints**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://localhost:8000/api/tasks/
   ```

3. **Test Property Endpoints**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://localhost:8000/api/properties/
   ```

### **Scenario 6: Permission Testing**
1. **Test Access Restrictions**:
   - Login as `staff_bob` → Try accessing admin panel (should be denied)
   - Login as `crew_charlie` → Try viewing other users' tasks
   - Login as `manager_alice` → Try creating superuser (should be limited)

### **Scenario 7: Search & Filter Testing**
1. **Manager Interface**:
   - Search tasks by property name
   - Filter tasks by status (pending, in-progress, completed)
   - Filter bookings by date range
2. **Staff Portal**:
   - Search assigned tasks
   - Filter by task type (cleaning, maintenance)

---

## 🔍 **Verification Checklist**

### **Authentication & Security:**
- [ ] Login works for all user types
- [ ] JWT tokens generate properly
- [ ] Permission restrictions enforced
- [ ] Rate limiting functional (try multiple rapid logins)

### **Task Management:**
- [ ] Tasks display with correct property associations
- [ ] Status updates save and reflect in UI
- [ ] Task assignment notifications work
- [ ] Field reference consistency (property_ref vs property)

### **Booking Management:**
- [ ] Bookings display with correct dates and guests
- [ ] Past vs future bookings properly categorized
- [ ] Property associations correct

### **Data Integrity:**
- [ ] No broken links or missing references
- [ ] Soft delete functionality working
- [ ] Audit logs capturing changes
- [ ] Search functionality returns accurate results

### **User Experience:**
- [ ] Navigation intuitive for each role
- [ ] Dashboard shows relevant information
- [ ] Forms validate properly
- [ ] Error messages helpful

---

## 🐛 **Known Issues to Test**

Based on our recent fixes, verify these specific areas:

1. **Field Reference Consistency**:
   - Task search by property name works
   - Task creation uses correct property_ref field
   - No FieldError exceptions in task management

2. **Notification System**:
   - Notifications display properly in staff portal
   - Read/unread status updates correctly
   - No field reference errors in notification templates

3. **Property Associations**:
   - Booking → Property relationship displays correctly
   - Task → Property relationship uses property_ref field
   - PropertyOwnership → Manager assignments work

---

## 📊 **Database Inspection**

**Check database directly:**
```bash
cd aristay_backend
python manage.py shell
```

```python
from api.models import *

# Verify user count
User.objects.count()  # Should be 9

# Verify task-property relationships
Task.objects.filter(property_ref__name='Sunset Villa')

# Verify booking associations
for booking in Booking.objects.all():
    print(f"{booking.guest_name} → {booking.property.name}")

# Check notifications
for notif in Notification.objects.all():
    print(f"{notif.recipient.username}: {notif.verb} → {notif.task.title}")
```

---

## 🔄 **Reset Test Data**

**If you need to reset:**
```bash
cd aristay_backend
python manage.py flush  # WARNING: Deletes all data
python manage.py create_test_data  # Recreate test data
```

---

## 📞 **Quick Links for Testing**

- **Manager Dashboard**: http://localhost:8000/manager/
- **Staff Tasks**: http://localhost:8000/api/staff/tasks/
- **Admin Users**: http://localhost:8000/admin/auth/user/
- **Admin Properties**: http://localhost:8000/admin/api/property/
- **Admin Tasks**: http://localhost:8000/admin/api/task/
- **API Documentation**: http://localhost:8000/api/ (if DRF browsable API enabled)

Happy testing! 🚀
