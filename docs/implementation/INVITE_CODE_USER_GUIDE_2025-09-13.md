# Invite Code Management - User Guide

**For Administrators and Managers**  
**Last Updated:** September 13, 2025

## 🎯 Quick Start

### For Administrators

1. **Access Admin Portal** - Go to `/admin/` and log in
2. **Navigate to Invite Codes** - Click "Invite Codes" in the API section
3. **Create New Code** - Click "Create New Invite Code" button
4. **Fill Form** - Select role, task group, and settings
5. **Generate Code** - Click "Create Invite Code" to generate

### For Managers

1. **Access Manager Portal** - Go to `/manager/` and log in
2. **Find Invite Codes** - Click "Invite Codes" in Quick Actions
3. **Create New Code** - Click "Create New Invite Code" button
4. **Fill Form** - Select role, task group, and settings
5. **Generate Code** - Click "Create Invite Code" to generate

## 📋 Step-by-Step Instructions

### Creating an Invite Code

#### Step 1: Access the Create Form

**Admin Portal:**
- Go to `/admin/invite-codes/`
- Click the "➕ Create New Invite Code" button

**Manager Portal:**
- Go to `/manager/invite-codes/`
- Click the "➕ Create New Invite Code" button

#### Step 2: Fill Out Basic Information

**Role Selection:**
- **Staff** - Basic user with limited permissions
- **Manager** - Can view all tasks and manage team members
- **Admin** - Full system access including user management
- **Viewer** - Read-only access to view tasks and information

**Task Group Selection:**
- **General** - Multi-purpose, flexible assignments
- **Cleaning** - Housekeeping, room cleaning, turnover
- **Maintenance** - Repairs, HVAC, plumbing, electrical
- **Laundry** - Linens, towels, bedding
- **Lawn/Pool** - Landscaping, pool maintenance, outdoor

#### Step 3: Configure Usage Settings

**Maximum Uses:**
- **1** - Single use only (recommended for security)
- **2-10** - Limited multiple uses
- **0** - Unlimited uses (use with caution)

**Expiration (Days):**
- **7** - Expires in 1 week
- **30** - Expires in 1 month
- **90** - Expires in 3 months
- **Leave blank** - No expiration (not recommended)

#### Step 4: Add Notes (Optional)

Add internal notes about the code's purpose:
- "New cleaning staff member"
- "Temporary contractor access"
- "Emergency access for maintenance"

#### Step 5: Create the Code

Click "Create Invite Code" to generate the code. The system will:
- Generate a unique 8-character code
- Save all settings
- Redirect to the code list
- Show success message with the code

### Managing Existing Codes

#### Viewing All Codes

**List View Features:**
- **Search** - Find codes by code, creator, or notes
- **Filter by Role** - Show only specific roles
- **Filter by Task Group** - Show only specific task groups
- **Filter by Status** - Show active, inactive, expired, or usable codes
- **Pagination** - Navigate through large lists

**Code Information Displayed:**
- Code (8-character identifier)
- Role and Task Group
- Created By (who created it)
- Status (Active, Inactive, Expired, Usable)
- Usage (how many times used / max uses)
- Expiration Date
- Created Date
- Action Buttons

#### Viewing Code Details

Click the "👁️" button to view detailed information:

**Basic Information:**
- Code identifier
- Role and Task Group
- Created By and Date

**Status & Usage:**
- Current status with color coding
- Usage statistics with progress bar
- Last used date (if applicable)

**Expiration:**
- Expiration date and time
- Time remaining (if not expired)

**Used By:**
- List of users who used the code
- User details and usage timestamps

#### Editing Codes

Click the "✏️" button to edit (unused codes only):

**Editable Fields:**
- Role (can change user permissions)
- Task Group (can change work assignments)
- Maximum Uses (can adjust usage limits)
- Expiration (can extend or remove expiration)
- Notes (can update internal notes)

**Non-Editable Fields:**
- Code (cannot change once created)
- Created By (cannot change creator)
- Used Count (cannot modify usage history)

#### Revoking Codes

Click the "🚫" button to revoke (deactivate) a code:

**What Happens:**
- Code becomes inactive
- Cannot be used for new registrations
- Existing users are not affected
- Code can be reactivated later

**When to Revoke:**
- Code has been compromised
- User no longer needs access
- Code is no longer needed
- Security concerns

#### Reactivating Codes

Click the "✅" button to reactivate a revoked code:

**What Happens:**
- Code becomes active again
- Can be used for new registrations
- All original settings are preserved
- Usage history is maintained

**When to Reactivate:**
- Code was revoked by mistake
- User needs access again
- Temporary revocation period ended

#### Deleting Codes

Click the "🗑️" button to permanently delete a code:

**Requirements:**
- Code must not have been used
- Cannot be undone
- All code data is permanently removed

**When to Delete:**
- Code was created by mistake
- Code is no longer needed
- Cleanup of unused codes

## 🔍 Filtering and Search

### Using Filters

**Role Filter:**
- Select specific roles to show only those codes
- Useful for managing codes by permission level

**Task Group Filter:**
- Select specific task groups to show only those codes
- Useful for managing codes by work type

**Status Filter:**
- **Active** - Currently usable codes
- **Inactive** - Revoked codes
- **Expired** - Codes past expiration date
- **Usable** - Active codes that are not expired

### Using Search

**Search by Code:**
- Enter the 8-character code
- Find specific codes quickly

**Search by Creator:**
- Enter creator's username
- Find codes created by specific users

**Search by Notes:**
- Enter keywords from notes
- Find codes by purpose or description

### Combining Filters

You can combine multiple filters and search:
- Filter by role AND task group
- Search within filtered results
- Use status filter with search terms

## 📊 Understanding Status

### Status Colors and Meanings

| Status | Color | Meaning | Actions Available |
|--------|-------|---------|------------------|
| **Active** | Green | Code is active and usable | View, Edit, Revoke, Delete |
| **Inactive** | Red | Code has been revoked | View, Reactivate, Delete |
| **Expired** | Yellow | Code has passed expiration | View, Reactivate, Delete |
| **Usable** | Blue | Code is active and not expired | View, Edit, Revoke, Delete |

### Status Transitions

```
Created → Active → Revoked → Reactivated → Active
   ↓         ↓         ↓
  Delete   Expired   Delete
```

## 📈 Usage Tracking

### Understanding Usage Metrics

**Used Count:**
- Shows how many times the code has been used
- Updates automatically when someone registers

**Max Uses:**
- Shows the maximum number of times the code can be used
- "∞" means unlimited uses

**Usage Percentage:**
- Visual progress bar showing usage
- Helps track code utilization

**Used By List:**
- Shows all users who used the code
- Includes usernames and usage timestamps

### Usage Rules

**Single Use Codes (Recommended):**
- Can only be used once
- Best for security
- Automatically becomes unusable after first use

**Multi-Use Codes:**
- Can be used multiple times up to max_uses
- Good for team invitations
- Becomes unusable when max_uses is reached

**Unlimited Codes:**
- Can be used unlimited times
- Use with caution
- Good for public registration links

## 🚨 Troubleshooting

### Common Issues

**"Access Denied" Error:**
- Check your user role
- Ensure you have permission to manage invite codes
- Contact administrator if needed

**"Code Not Found" Error:**
- Verify the code ID
- Check if code was deleted
- Refresh the page

**"Cannot Edit Used Code" Error:**
- Codes that have been used cannot be edited
- Create a new code instead
- Or revoke and create a new one

**"Form Validation Error":**
- Check all required fields are filled
- Ensure role and task group are valid
- Verify expiration days is a number

### Getting Help

**For Technical Issues:**
- Check the system logs
- Contact the development team
- Report bugs with detailed information

**For Permission Issues:**
- Contact your administrator
- Request role changes if needed
- Verify account status

**For Usage Questions:**
- Review the documentation
- Check with other administrators
- Contact support team

## 💡 Best Practices

### Security Best Practices

1. **Use Single-Use Codes** - Set max_uses to 1 for better security
2. **Set Expiration Dates** - Don't create permanent codes
3. **Regular Cleanup** - Remove unused expired codes
4. **Monitor Usage** - Track who is using codes
5. **Use Descriptive Notes** - Document code purposes

### Operational Best Practices

1. **Plan Code Creation** - Think about role and task group assignments
2. **Regular Review** - Periodically review and clean up codes
3. **Document Purposes** - Use notes to track code purposes
4. **Monitor Expiration** - Check for codes expiring soon
5. **Track Usage** - Monitor which codes are being used

### User Management Best Practices

1. **Role Assignment** - Assign appropriate roles for user needs
2. **Task Group Mapping** - Match codes to actual work assignments
3. **Access Control** - Only give invite code management to trusted users
4. **Regular Audits** - Review code usage and access patterns
5. **Cleanup Procedures** - Establish regular cleanup routines

## 📞 Support

### Getting Help

**Documentation:**
- This user guide
- Technical implementation guide
- API documentation

**Contact Information:**
- **System Administrator** - admin@aristay.com
- **Technical Support** - support@aristay.com
- **Development Team** - dev@aristay.com

**Emergency Support:**
- For urgent issues, contact the system administrator
- Include detailed error messages and steps to reproduce
- Provide screenshots if possible

### Reporting Issues

**Bug Reports:**
- Describe the problem clearly
- Include steps to reproduce
- Provide error messages
- Include browser and system information

**Feature Requests:**
- Describe the desired functionality
- Explain the business need
- Provide use cases
- Include mockups if possible

---

**Last Updated:** September 13, 2025  
**Version:** 2.0  
**Next Review:** October 13, 2025
