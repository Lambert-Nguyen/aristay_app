# Invite Code Management Guide - AriStay Admin

**For System Administrators**  
**Last Updated:** September 11, 2025

## 🎯 Overview

The Invite Code Management system allows administrators to control user registration by creating and managing invite codes. Each code automatically assigns users to specific roles and task groups upon registration.

## 🔑 Accessing Invite Code Management

### Admin Interface
1. **Login to Admin Panel**: Go to `/admin/` and log in with admin credentials
2. **Navigate to Invite Codes**: Click on "Invite Codes" in the API section
3. **Alternative URL**: Go directly to `/admin/invite-codes/`

### Permissions Required
- **Superuser Access**: Only superusers can manage invite codes
- **Admin Panel Access**: Must have access to Django admin interface

## 📋 Creating Invite Codes

### Step-by-Step Process

#### 1. Access Create Form
- Click **"Create New Invite Code"** button
- Or navigate to `/admin/create-invite-code/`

#### 2. Fill Out Basic Information
- **Role**: Select the user role (Member, Manager, Admin)
  - **Member**: Basic user with limited permissions
  - **Manager**: Can view all tasks and manage team members
  - **Admin**: Full system access including user management
- **Task Group**: Select the task group assignment
  - **General**: Multi-purpose, flexible assignments
  - **Cleaning**: Housekeeping, room cleaning, turnover
  - **Maintenance**: Repairs, HVAC, plumbing, electrical
  - **Laundry**: Linens, towels, bedding
  - **Lawn/Pool**: Landscaping, pool maintenance, outdoor

#### 3. Configure Usage Settings
- **Single Use**: Code can only be used once (recommended for security)
- **Multiple Use**: Set maximum number of uses
  - Enter a number (e.g., 5 for 5 uses)
  - Leave blank or 0 for unlimited uses

#### 4. Set Expiration (Optional)
- **No Expiration**: Leave blank for permanent codes
- **With Expiration**: Enter number of days (1-365)
  - Example: 30 days = code expires in 30 days

#### 5. Add Notes (Optional)
- **Internal Notes**: Add any notes about the code's purpose
- **Examples**: "New cleaning staff", "Temporary contractor", "Manager promotion"

#### 6. Create the Code
- Click **"Create Invite Code"**
- The system will generate a unique 8-character code
- **Example codes**: "ABC12345", "XYZ78901", "DEF45678"

## 📊 Managing Existing Codes

### Viewing All Codes
The admin interface shows all invite codes with:
- **Code**: The actual invite code
- **Created By**: Who created the code
- **Role**: User role assigned by the code
- **Task Group**: Task group assignment
- **Usage**: Current usage vs. maximum allowed
- **Status**: Active, Inactive, or Expired
- **Expires**: Expiration date (if set)
- **Created**: When the code was created

### Filtering and Searching
- **Filter by Role**: Show only Member, Manager, or Admin codes
- **Filter by Task Group**: Show codes for specific task groups
- **Filter by Status**: Show Active, Inactive, or Expired codes
- **Search**: Search by code, creator username, or notes

### Bulk Operations
1. **Select Codes**: Check the boxes next to codes you want to modify
2. **Choose Action**: Select from dropdown menu
   - **Deactivate selected invite codes**: Make codes unusable
   - **Activate selected invite codes**: Make codes usable again
   - **Export selected invite codes to CSV**: Download data
3. **Execute**: Click "Go" to perform the action

## 🔧 Code Management Actions

### Individual Code Actions

#### View Code Details
- Click on any code to view full details
- See usage history and statistics
- View all users who have used the code

#### Revoke a Code
- Click **"Revoke"** button next to any active code
- Confirms the action before revoking
- Revoked codes become unusable immediately

#### Copy Code
- Click **"Copy"** button to copy code to clipboard
- Useful for sharing codes via email or messaging
- Shows confirmation when copied

### Bulk Management

#### Deactivate Multiple Codes
1. Select codes using checkboxes
2. Choose "Deactivate selected invite codes"
3. Click "Go"
4. Confirms the number of codes being deactivated

#### Activate Multiple Codes
1. Select inactive codes
2. Choose "Activate selected invite codes"
3. Click "Go"
4. Makes all selected codes usable again

#### Export to CSV
1. Select codes to export
2. Choose "Export selected invite codes to CSV"
3. Downloads a CSV file with all code data
4. Includes: Code, Creator, Role, Task Group, Usage, Status, etc.

## 📈 Monitoring Usage

### Usage Statistics
- **Used Count**: How many times the code has been used
- **Max Uses**: Maximum allowed uses (0 = unlimited)
- **Usage Bar**: Visual indicator of usage percentage
- **Last Used**: When the code was last used

### Status Indicators
- **🟢 Active**: Code is usable and not expired
- **🔴 Inactive**: Code has been manually deactivated
- **🟡 Expired**: Code has passed its expiration date
- **⚠️ Warning**: Code is near its usage limit

### Real-Time Monitoring
- **Live Updates**: Statistics update in real-time
- **Usage Tracking**: See which users have used each code
- **Expiration Alerts**: Visual indicators for expiring codes

## 🚨 Troubleshooting Common Issues

### Code Not Working
**Symptoms**: Users get "Invalid invite code" error

**Possible Causes:**
- Code has expired
- Code has been deactivated
- Code has reached usage limit
- Code doesn't exist

**Solutions:**
1. Check code status in admin interface
2. Verify expiration date
3. Check usage count vs. maximum
4. Create new code if necessary

### User Registration Fails
**Symptoms**: User can't complete registration

**Possible Causes:**
- Username already exists
- Email already exists
- Password doesn't meet requirements
- System error

**Solutions:**
1. Check error message in registration form
2. Verify username/email uniqueness
3. Ensure password meets requirements (8+ characters)
4. Check system logs for errors

### Admin Access Issues
**Symptoms**: Can't access invite code management

**Possible Causes:**
- Not logged in as superuser
- Insufficient permissions
- URL routing issue

**Solutions:**
1. Ensure you're logged in as superuser
2. Check user permissions
3. Verify URL configuration
4. Contact system administrator

## 🔒 Security Best Practices

### Code Security
- **Keep Codes Private**: Don't share codes in public channels
- **Use Single-Use Codes**: For maximum security, use single-use codes
- **Set Expiration**: Use expiration dates for temporary access
- **Monitor Usage**: Regularly check usage statistics

### Access Control
- **Limit Admin Access**: Only give admin access to trusted users
- **Regular Audits**: Periodically review all invite codes
- **Revoke Unused Codes**: Deactivate codes that are no longer needed
- **Track Usage**: Monitor who is using codes and when

### Data Protection
- **Secure Storage**: Codes are stored securely in the database
- **Access Logging**: All admin actions are logged
- **Backup Codes**: Export codes regularly for backup
- **Clean Up**: Remove old, unused codes periodically

## 📊 Reporting and Analytics

### Usage Reports
- **Total Codes Created**: Count of all invite codes
- **Active Codes**: Currently usable codes
- **Used Codes**: Codes that have been used
- **Expired Codes**: Codes that have expired

### User Analytics
- **Registration Success Rate**: Percentage of successful registrations
- **Most Popular Roles**: Which roles are most commonly assigned
- **Task Group Distribution**: Distribution of task group assignments
- **Code Usage Patterns**: When and how often codes are used

### Export Options
- **CSV Export**: Download detailed code data
- **Filtered Exports**: Export only specific codes
- **Usage Reports**: Export usage statistics
- **Audit Logs**: Export admin action logs

## 🚀 Advanced Features

### Code Templates
Consider creating templates for common scenarios:
- **New Employee**: Member role, General task group, 1 use, 30 days
- **Manager Promotion**: Manager role, specific task group, 1 use, 7 days
- **Temporary Contractor**: Member role, specific task group, 1 use, 90 days

### Integration with HR Systems
- **Bulk Import**: Import codes from HR systems
- **Automated Creation**: Create codes automatically for new employees
- **Role Synchronization**: Sync roles with HR databases

### Custom Workflows
- **Approval Process**: Require approval before code creation
- **Notification System**: Notify users when codes are created
- **Integration APIs**: Connect with external systems

## 📞 Support and Maintenance

### Regular Maintenance
- **Weekly**: Review active codes and usage
- **Monthly**: Clean up expired and unused codes
- **Quarterly**: Audit all codes and permissions
- **Annually**: Review and update security policies

### Backup and Recovery
- **Regular Exports**: Export code data regularly
- **Database Backups**: Ensure database backups include invite codes
- **Disaster Recovery**: Have a plan for code recovery

### Monitoring and Alerts
- **Usage Alerts**: Set up alerts for unusual usage patterns
- **Expiration Alerts**: Get notified when codes are about to expire
- **Error Monitoring**: Monitor for registration errors

---

**Remember**: Invite codes are a critical security feature. Always follow security best practices and regularly monitor code usage.

**For technical support or advanced configuration, contact the development team.**
