# Lost & Found Feature - User Guide

**Date:** September 9, 2025  
**Version:** 1.0  
**Audience:** Staff Members, Property Managers  

## 🎯 Overview

The Lost & Found feature allows staff members to report and manage items found during their work at properties. This guide explains how to use the feature effectively in both the staff portal and admin interface.

## 🔍 How to Report a Lost & Found Item

### From Task Detail View

1. **Navigate to a Task**
   - Go to the staff portal dashboard
   - Click on any task to open the task detail view

2. **Open Lost & Found Modal**
   - Look for the "🔍 Report Lost & Found" button in the quick actions section
   - Click the button to open the reporting modal

3. **Fill Out the Form**
   - **Item Title** (Required): Enter a clear, descriptive title
     - Example: "iPhone 12 Pro", "Wedding Ring", "Black Backpack"
   - **Description** (Required): Provide detailed description
     - Example: "Black iPhone 12 Pro with cracked screen, no case"
   - **Category** (Optional): Select from dropdown
     - Options: Electronics, Clothing, Jewelry, Personal Items, Documents, Toys, Other
   - **Estimated Value** (Optional): Enter dollar amount
     - Example: 500.00
   - **Found Location** (Required): Where the item was found
     - Example: "Master bedroom under bed", "Kitchen counter"
   - **Storage Location** (Optional): Where the item will be stored
     - Example: "Office safe", "Front desk drawer"
   - **Additional Notes** (Optional): Any extra information
     - Example: "Found during cleaning, guest left behind"

4. **Submit the Report**
   - Click "Report Item" to submit
   - You'll see a success notification
   - The modal will close and redirect to the Lost & Found dashboard

### From Lost & Found Dashboard

1. **Navigate to Lost & Found**
   - Click "Lost & Found" in the main navigation
   - This shows all items you have access to

2. **View Item Details**
   - Each item shows:
     - Title and description
     - Property location
     - Found location
     - Status (Found, Claimed, Disposed, Donated)
     - Found date and who found it
     - Estimated value (if provided)

3. **Filter Items**
   - Use the status dropdown to filter by:
     - All Statuses
     - Found
     - Claimed
     - Disposed
     - Donated
   - Click "Filter" to apply

## 📊 Understanding Item Status

### Status Types

- **Found**: Item has been reported but not yet claimed
- **Claimed**: Item has been claimed by its owner
- **Disposed**: Item has been disposed of (thrown away, donated, etc.)
- **Donated**: Item has been donated to charity

### Status Workflow

1. **Found** → **Claimed**: When owner claims the item
2. **Found** → **Disposed**: When item is disposed of
3. **Found** → **Donated**: When item is donated

## 🔧 Admin Interface (For Managers)

### Accessing Admin Interface

1. **Login to Admin**
   - Go to `/admin/` in your browser
   - Login with your admin credentials

2. **Navigate to Lost & Found**
   - Click "Lost Found Items" in the API section
   - This shows all lost & found items in the system

### Managing Items

#### Viewing Items
- **List View**: Shows all items with key information
- **Search**: Use the search box to find specific items
- **Filter**: Use filters to narrow down results

#### Editing Items
1. **Click on an Item**: Opens the detailed edit form
2. **Update Information**: Modify any field as needed
3. **Save Changes**: Click "Save" to update the item

#### History Tracking
- **View History**: Click "History" button to see all changes
- **Change Details**: Shows who made changes and when
- **Before/After Values**: Shows old and new values for each change

### Admin Features

#### Bulk Actions
- Select multiple items using checkboxes
- Perform bulk status updates
- Export item lists

#### Advanced Filtering
- Filter by property
- Filter by status
- Filter by date range
- Filter by category

## 📱 Mobile Usage

### Responsive Design
- The Lost & Found feature works on all devices
- Forms are optimized for mobile screens
- Touch-friendly buttons and inputs

### Mobile Tips
- Use landscape mode for better form viewing
- Tap and hold for context menus
- Swipe to navigate between items

## 🔒 Permissions and Access

### Staff Members
- Can report new items
- Can view items from their assigned properties
- Can view items they found themselves
- Cannot edit items created by others

### Managers
- Can view all items
- Can edit any item
- Can change item status
- Can access admin interface

### Superusers
- Full access to all features
- Can delete items
- Can access all admin functions

## 📋 Best Practices

### Reporting Items

1. **Be Descriptive**
   - Use clear, specific titles
   - Provide detailed descriptions
   - Include identifying features

2. **Location Accuracy**
   - Be specific about where item was found
   - Include room, area, or specific location
   - Note any relevant context

3. **Value Estimation**
   - Provide realistic value estimates
   - Consider condition and age
   - Note if value is unknown

4. **Timely Reporting**
   - Report items as soon as possible
   - Don't wait to report multiple items
   - Update status promptly when claimed

### Managing Items

1. **Regular Updates**
   - Check for new items regularly
   - Update status when items are claimed
   - Clean up old, disposed items

2. **Communication**
   - Notify relevant staff about new items
   - Update guests about found items
   - Coordinate with property managers

3. **Documentation**
   - Keep detailed notes about item handling
   - Document disposal or donation decisions
   - Maintain proper records

## 🚨 Troubleshooting

### Common Issues

#### Can't See Lost & Found Button
- **Check Permissions**: Ensure you have proper access
- **Refresh Page**: Try refreshing the browser
- **Contact Manager**: Ask manager to verify permissions

#### Modal Won't Open
- **Check JavaScript**: Ensure JavaScript is enabled
- **Clear Cache**: Clear browser cache and cookies
- **Try Different Browser**: Test in different browser

#### Can't Submit Form
- **Check Required Fields**: Ensure all required fields are filled
- **Check Internet**: Verify internet connection
- **Try Again**: Wait a moment and try again

#### Items Not Showing
- **Check Filters**: Verify filter settings
- **Check Permissions**: Ensure you have access to the property
- **Contact Support**: If issue persists, contact technical support

### Getting Help

#### Self-Service
- Check this user guide
- Look for error messages
- Try refreshing the page

#### Contact Support
- **Technical Issues**: Contact IT support
- **Permission Issues**: Contact your manager
- **Feature Questions**: Contact property management

## 📞 Support Information

### Technical Support
- **Email**: support@aristay.com
- **Phone**: (555) 123-4567
- **Hours**: Monday-Friday, 9 AM - 5 PM

### Training Resources
- **Video Tutorials**: Available in staff portal
- **Documentation**: This guide and technical docs
- **Training Sessions**: Monthly group training available

### Feedback
- **Feature Requests**: Submit via staff portal
- **Bug Reports**: Use the feedback form
- **Suggestions**: Email suggestions to management

## 📚 Additional Resources

### Related Features
- **Task Management**: How tasks relate to lost & found
- **Property Management**: Property-specific item tracking
- **Guest Communication**: Notifying guests about found items

### Documentation
- **Technical Guide**: For developers and IT staff
- **Admin Guide**: For managers and administrators
- **API Documentation**: For system integrations

### Training Materials
- **Quick Start Guide**: Get up and running quickly
- **Video Tutorials**: Step-by-step video guides
- **FAQ**: Frequently asked questions

---

**Document Version:** 1.0  
**Last Updated:** September 9, 2025  
**Next Review:** December 9, 2025  
**Maintained By:** Property Management Team

## 📝 Quick Reference

### Keyboard Shortcuts
- **Ctrl + F**: Search for items
- **Esc**: Close modal
- **Enter**: Submit form

### Status Icons
- 🔍 **Found**: Item reported, not claimed
- ✅ **Claimed**: Item claimed by owner
- 🗑️ **Disposed**: Item disposed of
- ❤️ **Donated**: Item donated to charity

### Contact Information
- **Emergency**: (555) 911-HELP
- **General**: (555) 123-4567
- **Email**: help@aristay.com
