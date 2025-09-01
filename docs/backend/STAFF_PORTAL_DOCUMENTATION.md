# 👥 AriStay Staff Portal Documentation

## 🌟 Overview

The AriStay Staff Portal provides specialized web interfaces for different types of property management staff. Each role has a customized dashboard and workflow optimized for their specific responsibilities.

## 🔐 Access & Authentication

### Entry Point
- **Main URL**: `/api/staff/`
- **Authentication**: Login required - redirects to unified login if not authenticated
- **Role-based routing**: Automatically routes users to their specialized dashboard

### Role-based Redirections
```
Superuser → /admin/ (Admin interface)
Manager → /manager/ (Manager interface)  
Cleaning Staff → /api/staff/cleaning/
Maintenance Staff → /api/staff/maintenance/
Laundry Staff → /api/staff/laundry/
Lawn/Pool Staff → /api/staff/lawn_pool/
Viewer → /api/portal/properties/ (Read-only)
Default Staff → /api/staff/tasks/ (Task list)
```

## 🧽 Cleaning Staff Interface

### Dashboard Features (`/api/staff/cleaning/`)
- **📊 Statistics**: Total assigned, due today, upcoming, average progress
- **🚨 Priority Tasks**: Overdue and today's tasks with progress tracking
- **📋 Interactive Checklists**: Room-by-room completion tracking
- **📸 Photo Requirements**: Upload proof of work completion
- **📅 Upcoming Schedule**: 7-day lookahead with progress indicators

### Checklist System
- **Room Organization**: Bathroom, bedroom, kitchen, living room sections
- **Item Types**:
  - ✅ Check items (simple completion)
  - 📷 Photo required/optional (visual proof)
  - ✏️ Text input (detailed notes)
  - 🔢 Number input (quantities, counts)
  - 🚫 Blocking steps (must complete before proceeding)
- **Real-time Progress**: Automatic completion percentage calculation
- **Auto-save**: Text inputs save automatically after typing stops

### Workflow
1. **View Dashboard** → See assigned cleaning tasks
2. **Select Task** → Access detailed checklist
3. **Complete Checklist** → Check off items, upload photos, add notes
4. **Submit Task** → Mark as complete when checklist is 100%

## 🔧 Maintenance Staff Interface

### Dashboard Features (`/api/staff/maintenance/`)
- **📊 Statistics**: Total assigned, overdue, due today, low stock alerts
- **🚨 Priority Alerts**: Overdue tasks highlighted in red
- **📦 Inventory Monitoring**: Low stock items across all properties
- **📊 Transaction History**: Recent inventory movements by user
- **🛠️ Quick Actions**: Direct access to tools and inventory

### Inventory Management
- **Stock Tracking**: Real-time inventory levels per property
- **Par Level Alerts**: Automatic low-stock notifications
- **Transaction Logging**: Record stock movements with context
- **Color-coded Status**:
  - 🟢 Normal: Above par level
  - 🟡 Low Stock: At or below par level  
  - 🔴 Out of Stock: Zero quantity
  - 🔵 Overstocked: Above maximum level

### Maintenance Workflow
1. **Check Dashboard** → Review overdue/today's tasks + inventory alerts
2. **Complete Tasks** → Follow maintenance checklist
3. **Update Inventory** → Log used supplies and restock needs
4. **Report Issues** → Document problems in task notes

## 🧺 Laundry Staff Interface

### Dashboard Features (`/api/staff/laundry/`)
- **📊 Workflow Stages**: Pick-up, processing, delivery tracking
- **📝 Linen Counting**: Number input tracking for accountability
- **🏠 Property Overview**: Linen inventory per location
- **📅 Schedule Management**: Organized by workflow stage

### Laundry Workflow
1. **Pick-up Stage** → Count and photograph dirty linens
2. **Processing Stage** → Track wash/dry completion
3. **Quality Check** → Inspect for damage or stains
4. **Delivery Stage** → Count and deliver clean linens
5. **Restock** → Update linen inventory levels

## 🌿 Lawn/Pool Staff Interface

### Dashboard Features (`/api/staff/lawn_pool/`)
- **🗺️ Route Planning**: Tasks grouped by property for efficiency
- **🏊 Pool Chemistry**: Chemical inventory and testing supplies
- **📅 Seasonal Tasks**: Weather-dependent scheduling
- **📸 Progress Photos**: Before/after documentation

### Specialized Features
- **Property Grouping**: Tasks organized for route optimization
- **Chemical Tracking**: Pool & spa supply monitoring
- **Weather Integration**: Future enhancement for seasonal scheduling
- **GPS Check-in**: Future enhancement for location verification

## 📋 Universal Features (All Staff)

### My Tasks Interface (`/api/staff/tasks/`)
- **🔍 Advanced Filtering**: Status, type, property, date ranges
- **🔎 Search Functionality**: Full-text search across tasks
- **📄 Pagination**: Efficient handling of large task lists
- **📊 Progress Tracking**: Visual completion indicators

### Task Detail Interface (`/api/staff/tasks/{id}/`)
- **📋 Complete Checklist**: Interactive item completion
- **📸 Photo Management**: Upload, view, update images
- **✏️ Note Taking**: Context and issue reporting
- **⏱️ Real-time Updates**: AJAX-powered without page reloads
- **🔒 Permission Control**: Edit only assigned tasks

### Lost & Found (`/api/staff/lost-found/`)
- **📝 Item Logging**: Found item documentation
- **📸 Photo Evidence**: Visual identification
- **🏠 Property Association**: Link to specific locations
- **📅 Lifecycle Tracking**: Found → Claimed → Disposed

## 🎨 User Interface Design

### Design System
- **🎨 Color Scheme**: Purple gradient theme with role-specific accents
- **📱 Responsive**: Mobile-first design for tablet/phone use
- **♿ Accessibility**: High contrast, large touch targets
- **⚡ Performance**: Optimized loading, lazy image loading

### Visual Elements
- **📊 Progress Bars**: Animated completion tracking
- **🏷️ Status Badges**: Color-coded task/inventory status
- **🔔 Alert Cards**: Priority task highlighting
- **📈 Statistics Cards**: Key metrics dashboard

### Navigation
- **🏠 Breadcrumb**: Clear location awareness
- **🔗 Role-specific Menu**: Contextual navigation options
- **🔄 Quick Actions**: One-click access to common tasks
- **↩️ Back Navigation**: Intuitive workflow progression

## 🔧 Technical Implementation

### Backend Architecture
- **🏗️ Django Views**: Role-specific view classes
- **🔐 Permission System**: User role validation
- **📊 Database Queries**: Optimized with `select_related`/`prefetch_related`
- **🚀 AJAX Endpoints**: Real-time updates without page refresh

### Frontend Technology
- **🎨 Pure CSS**: No external dependencies
- **⚡ Vanilla JavaScript**: Lightweight interactions
- **📱 CSS Grid**: Responsive layout system
- **🎭 CSS Animations**: Smooth transitions and feedback

### Security Features
- **🔐 CSRF Protection**: All form submissions protected
- **👤 User Authentication**: Login required for all features
- **🛡️ Permission Checks**: Role-based access control
- **📝 Audit Logging**: User action tracking

## 📱 Mobile Optimization

### Responsive Design
- **📱 Mobile-first**: Optimized for phone/tablet use
- **👆 Touch-friendly**: Large buttons and touch targets
- **📊 Adaptive Layouts**: Stacks on smaller screens
- **🔄 Offline Capability**: Future enhancement

### Performance
- **⚡ Fast Loading**: Minimal external resources
- **🗜️ Optimized Images**: Automatic compression
- **📡 Progressive Enhancement**: Works without JavaScript
- **💾 Local Storage**: Settings persistence

## 🔄 Integration Points

### API Connectivity
- **🔌 DRF Backend**: Uses existing Django REST Framework APIs
- **🔗 Session Auth**: Web portal session authentication
- **📡 Real-time Updates**: AJAX for instant feedback
- **🔄 Sync**: Consistent with mobile app data

### External Systems
- **📅 Calendar Integration**: Booking import system
- **📊 Reporting**: Data flows to admin dashboards
- **📱 Mobile App**: Shared data models and APIs
- **🔔 Notifications**: Integration with push notification system

## 🚀 Future Enhancements

### Phase 2 Features
- **💬 In-app Chat**: Staff ↔ Manager communication
- **📍 GPS Integration**: Location verification
- **🤖 AI Photo QA**: Automated quality checking
- **📊 Advanced Analytics**: Performance tracking

### Technical Improvements
- **🔄 WebSocket**: Real-time updates
- **📱 PWA**: Progressive Web App capabilities
- **🌐 Offline Mode**: Works without internet
- **🔔 Push Notifications**: Browser notifications

## 📞 Support & Training

### Getting Started
1. **🔐 Login**: Use your assigned credentials
2. **🏠 Dashboard**: Familiarize with your role interface
3. **📋 First Task**: Complete sample checklist
4. **📸 Photos**: Practice photo upload workflow
5. **💬 Questions**: Contact manager for support

### Best Practices
- **📸 Good Photos**: Well-lit, clear, relevant
- **✏️ Detailed Notes**: Document issues thoroughly
- **⏰ Timely Updates**: Update progress regularly
- **🔍 Quality Check**: Review work before submission
- **📞 Communication**: Report problems immediately

---

## 🎯 Quick Start Guide

### For Cleaning Staff:
1. Visit `/api/staff/` → Auto-redirected to cleaning dashboard
2. Check "Due Today" tasks first
3. Click task → Complete room-by-room checklist
4. Upload required photos, add notes
5. Mark complete when progress hits 100%

### For Maintenance Staff:
1. Visit `/api/staff/` → Auto-redirected to maintenance dashboard
2. Check overdue tasks (red alerts) first
3. Review low stock inventory alerts
4. Complete maintenance checklist
5. Log any inventory usage

### For All Staff:
- **📋 My Tasks**: `/api/staff/tasks/` - All assigned tasks
- **🔍 Lost & Found**: `/api/staff/lost-found/` - Item reporting
- **📊 Dashboard**: Role-specific homepage
- **🚪 Logout**: Top-right corner

The staff portal provides a comprehensive, user-friendly interface that makes property management tasks efficient and accountable. Each role gets exactly the tools and information they need, when they need it.
