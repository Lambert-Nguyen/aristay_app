# AriStay Dual Timezone Implementation Guide

## Overview

AriStay now supports dual timezone display throughout the application with Tampa, Florida (Eastern Time) as the default server timezone and user-specific timezone preferences.

## Key Features

### 🕐 **Dual Timezone Display**
- Shows both user's local timezone and Tampa, FL timezone side by side
- Example: `Aug 29, 2025 18:00 (San Jose, CA) | Aug 29, 2025 21:00 (Tampa, FL)`

### 🌍 **Server Default**
- **Default Timezone**: `America/New_York` (Tampa, FL - Eastern Time)
- **Display Name**: "Tampa, FL"
- **Fallback**: All users without timezone preference default to Tampa, FL

### 👤 **User Preferences**
- Users can set their local timezone in their profile
- Available timezones include major US cities and international locations
- Automatic dual display when user timezone differs from server timezone

## Template Usage

### Load the Template Tags
```django
{% load timezone_tags %}
```

### Display Filters

#### 1. **Dual Timezone Filter**
Shows both user and Tampa timezone:
```django
{{ task.created_at|dual_timezone:user }}
<!-- Output: Aug 29, 2025 18:00 (San Jose, CA) | Aug 29, 2025 21:00 (Tampa, FL) -->
```

#### 2. **User Timezone Only**
Shows only user's timezone:
```django
{{ task.due_date|user_timezone:user }}
<!-- Output: Aug 29, 2025 18:00 (San Jose, CA) -->
```

#### 3. **Tampa Timezone Only** (for logs and critical areas)
```django
{{ log.timestamp|tampa_timezone }}
<!-- Output: Aug 29, 2025 21:00 (Tampa, FL) -->
```

### Template Tags

#### 1. **Current Time Dual**
```django
{% current_time_dual user %}
<!-- Output: Current time: Aug 29, 2025 18:00 (San Jose, CA) | Server time: Aug 29, 2025 21:00 (Tampa, FL) -->
```

#### 2. **Timezone Info** (for JavaScript)
```django
{% timezone_info user as tz_info %}
{{ tz_info.user_timezone_name }}  <!-- San Jose, CA -->
{{ tz_info.server_timezone_name }} <!-- Tampa, FL -->
```

#### 3. **Available Timezone Choices**
```django
{% get_timezone_choices as timezones %}
{% for value, display in timezones %}
    <option value="{{ value }}">{{ display }}</option>
{% endfor %}
```

## Available Timezones

| Value | Display Name | Use Case |
|-------|-------------|----------|
| `America/New_York` | Eastern Time (Tampa, FL) | **Default server timezone** |
| `America/Los_Angeles` | Pacific Time (San Jose, CA) | West Coast operations |
| `America/Chicago` | Central Time (Chicago, IL) | Central US |
| `America/Denver` | Mountain Time (Denver, CO) | Mountain US |
| `America/Phoenix` | Arizona Time (Phoenix, AZ) | Arizona (no DST) |
| `America/Anchorage` | Alaska Time (Anchorage, AK) | Alaska operations |
| `Pacific/Honolulu` | Hawaii Time (Honolulu, HI) | Hawaii operations |
| `Asia/Ho_Chi_Minh` | Vietnam Time (Ho Chi Minh City) | Vietnam operations |
| `Europe/London` | GMT/BST (London, UK) | UK operations |
| `UTC` | UTC (Coordinated Universal Time) | Technical/logging |

## Implementation Examples

### 1. **Portal Templates**
```django
{% load timezone_tags %}

<!-- Task due date with dual timezone -->
<div>Due: {{ task.due_date|dual_timezone:user }}</div>

<!-- Current time display in header -->
<div>{% current_time_dual user %}</div>
```

### 2. **Admin Templates**
```django
{% load timezone_tags %}

<!-- System metrics timestamp -->
<p>Last updated: {{ metrics.timestamp|dual_timezone:user }}</p>

<!-- Log viewer (Tampa only for consistency) -->
<div>{{ log_entry.timestamp|tampa_timezone }}</div>
```

### 3. **Staff Portal**
```django
{% load timezone_tags %}

<!-- Task creation time -->
<strong>Created:</strong> {{ task.created_at|dual_timezone:user }}

<!-- Modified time -->
<strong>Modified:</strong> {{ task.modified_at|dual_timezone:user }}
```

## Database Configuration

### Profile Model
```python
class Profile(models.Model):
    TIMEZONE_CHOICES = [
        ('America/New_York', 'Eastern Time (Tampa, FL)'),
        ('America/Los_Angeles', 'Pacific Time (San Jose, CA)'),
        # ... other choices
    ]
    
    timezone = models.CharField(
        max_length=32,
        choices=TIMEZONE_CHOICES,
        default='America/New_York',  # Tampa, FL default
        help_text="Your local timezone for displaying dates and times"
    )
```

### Django Settings
```python
TIME_ZONE = "America/New_York"  # Tampa, FL (Eastern Time)
ARISTAY_DEFAULT_TIMEZONE = "America/New_York"
ARISTAY_TIMEZONE_DISPLAY_NAME = "Tampa, FL"
USE_TZ = True
```

## Display Guidelines

### **When to Use Dual Timezone**
- ✅ Task timestamps (created, modified, due dates)
- ✅ User activity logs
- ✅ Dashboard time displays
- ✅ Booking times
- ✅ Notification timestamps

### **When to Use Tampa Timezone Only**
- ✅ System logs (debug.log, error.log)
- ✅ Performance metrics
- ✅ Security logs
- ✅ Database timestamps for debugging
- ✅ Server health checks

### **Display Format Examples**

#### Good Examples:
```
Created: Aug 29, 2025 18:00 (San Jose, CA) | Aug 29, 2025 21:00 (Tampa, FL)
Due: Aug 30, 2025 09:00 (Ho Chi Minh, Vietnam) | Aug 29, 2025 22:00 (Tampa, FL)
Current time: Aug 29, 2025 18:00 (San Jose, CA) | Server time: Aug 29, 2025 21:00 (Tampa, FL)
```

#### Same Timezone (Tampa user):
```
Created: Aug 29, 2025 21:00 (Tampa, FL)
Current time: Aug 29, 2025 21:00 (Tampa, FL)
```

## Benefits

### **For Users**
- 🌍 See times in their local timezone
- 🏢 Always know server time (Tampa, FL)
- 🕐 No confusion about when things actually happened
- 📅 Easy scheduling across timezones

### **For Operations**
- 🔧 Consistent server time reference (Tampa, FL)
- 📊 Easier log analysis with single timezone
- 👥 Better coordination across distributed team
- 🎯 Clear context for all timestamps

### **For Development**
- 🛡️ Timezone-aware throughout the application
- 📝 Easy template implementation
- 🔄 Consistent user experience
- ⚡ Automatic timezone detection and display

## Migration Notes

- Default timezone changed from UTC to America/New_York (Tampa, FL)
- Existing users without timezone preference default to Tampa, FL
- All existing timestamps remain in database as UTC (recommended)
- Display layer converts to appropriate timezones automatically

This implementation provides a professional, user-friendly timezone experience that scales across multiple locations while maintaining Tampa, FL as the operational center.
