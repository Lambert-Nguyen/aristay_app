# User Registration System with Invite Codes

**Implementation Date:** September 11, 2025  
**Version:** 1.0  
**Status:** ✅ Complete and Production Ready

## Overview

The AriStay User Registration System implements a secure, invite-code-based user registration process that allows administrators to control user access and automatically assign roles and task groups. This system ensures that only authorized users can create accounts while providing a seamless registration experience.

## 🎯 Key Features

### For Administrators
- **Invite Code Management**: Create, view, and manage invite codes through a comprehensive admin interface
- **Role Assignment**: Automatically assign user roles (Member, Manager, Admin) based on invite code
- **Task Group Assignment**: Assign users to specific task groups (Cleaning, Maintenance, Laundry, etc.)
- **Usage Tracking**: Monitor invite code usage with real-time statistics
- **Expiration Control**: Set optional expiration dates for time-limited access
- **Bulk Operations**: Activate/deactivate multiple codes, export to CSV

### For New Users
- **Simple Registration**: Clean, intuitive registration form with real-time validation
- **Automatic Assignment**: Users are automatically assigned roles and task groups based on their invite code
- **Immediate Access**: Users are automatically logged in after successful registration
- **Mobile Ready**: Full API support for mobile app integration

## 🏗️ System Architecture

### Core Components

#### 1. InviteCode Model
```python
class InviteCode(models.Model):
    code = models.CharField(max_length=32, unique=True, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    task_group = models.CharField(max_length=50, choices=TaskGroup.choices)
    role = models.CharField(max_length=20, choices=[('member', 'Member'), ...])
    max_uses = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # ... additional fields
```

#### 2. Registration Views
- **Web Registration**: `registration_view()` - HTML form-based registration
- **API Registration**: `register_user()` - REST API endpoint for mobile apps
- **Code Validation**: `validate_invite_code()` - Validate codes without registration

#### 3. Admin Interface
- **InviteCode Admin**: Full CRUD interface with filtering and search
- **Management Templates**: Custom admin templates for code management
- **Bulk Actions**: Mass operations on invite codes

## 📱 User Interface

### Registration Form (`/register/`)
- **Clean Design**: Modern, responsive form with real-time validation
- **Field Validation**: Client-side and server-side validation
- **Error Handling**: User-friendly error messages
- **Auto-formatting**: Invite codes are automatically formatted (uppercase, alphanumeric)

### Admin Interface (`/admin/invite-codes/`)
- **Code Management**: List, create, edit, and delete invite codes
- **Usage Statistics**: Real-time usage tracking with visual indicators
- **Filtering**: Filter by role, task group, status, and creation date
- **Bulk Operations**: Select multiple codes for batch operations

### Login Integration
- **Registration Link**: "Register with invite code" link on login screen
- **Seamless Flow**: Direct navigation from login to registration

## 🔐 Security Features

### Code Generation
- **Cryptographically Secure**: Uses Python's `secrets` module
- **Unique Codes**: 8-character alphanumeric codes with collision detection
- **Format**: Uppercase letters and numbers only (e.g., "ABC12345")

### Access Control
- **Role-Based Assignment**: Automatic role assignment based on invite code
- **Task Group Isolation**: Users are assigned to specific task groups
- **Usage Limits**: Single-use or multi-use codes with configurable limits
- **Expiration Control**: Optional time-based expiration

### Validation
- **Server-Side Validation**: All inputs validated on the server
- **Code Verification**: Invite codes are verified before user creation
- **Duplicate Prevention**: Username and email uniqueness enforced
- **Password Requirements**: Minimum 8 characters with confirmation

## 🚀 API Endpoints

### Registration API

#### Register User
```http
POST /api/register/
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepass123",
  "password_confirm": "securepass123",
  "first_name": "John",
  "last_name": "Doe",
  "invite_code": "ABC12345"
}
```

**Response (Success):**
```json
{
  "success": true,
  "user_id": 123,
  "username": "newuser",
  "role": "member",
  "task_group": "cleaning"
}
```

**Response (Error):**
```json
{
  "error": "Invalid invite code"
}
```

#### Validate Invite Code
```http
POST /api/validate-invite/
Content-Type: application/json

{
  "code": "ABC12345"
}
```

**Response:**
```json
{
  "valid": true,
  "role": "member",
  "task_group": "cleaning",
  "expires_at": "2025-12-31T23:59:59Z",
  "max_uses": 1,
  "used_count": 0
}
```

### Admin API

#### List Invite Codes
```http
GET /admin/invite-codes/
```

#### Create Invite Code
```http
POST /admin/create-invite-code/
Content-Type: application/x-www-form-urlencoded

role=member&task_group=cleaning&max_uses=1&expires_days=30&notes=New cleaning staff
```

#### Revoke Invite Code
```http
POST /admin/revoke-invite-code/123/
```

## 🗄️ Database Schema

### InviteCode Table
```sql
CREATE TABLE api_invitecode (
    id SERIAL PRIMARY KEY,
    code VARCHAR(32) UNIQUE NOT NULL,
    created_by_id INTEGER NOT NULL REFERENCES auth_user(id),
    task_group VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL,
    max_uses INTEGER NOT NULL DEFAULT 1,
    used_count INTEGER NOT NULL DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    notes TEXT
);
```

### Usage Tracking
- **used_by**: Many-to-many relationship tracking which users used each code
- **used_count**: Integer field for quick usage statistics
- **last_used_at**: Timestamp of most recent usage

## 🧪 Testing

### Test Coverage
- **Model Tests**: InviteCode creation, expiration, usage tracking
- **API Tests**: Registration endpoints, validation, error handling
- **Admin Tests**: Admin interface functionality
- **Security Tests**: Code generation, validation, access control

### Test Files
- `tests/unit/test_invite_code_system.py` - Comprehensive test suite

### Running Tests
```bash
# Run all invite code tests
python -m pytest tests/unit/test_invite_code_system.py -v

# Run specific test class
python -m pytest tests/unit/test_invite_code_system.py::TestInviteCodeModel -v
```

## 📋 Usage Guide

### For Administrators

#### Creating Invite Codes
1. Navigate to `/admin/invite-codes/`
2. Click "Create New Invite Code"
3. Select role (Member, Manager, Admin)
4. Select task group (Cleaning, Maintenance, Laundry, etc.)
5. Set usage limit (1 for single-use, higher for multi-use, 0 for unlimited)
6. Set expiration (optional)
7. Add notes (optional)
8. Click "Create Invite Code"

#### Managing Invite Codes
1. View all codes in the admin interface
2. Use filters to find specific codes
3. Select codes for bulk operations
4. Export codes to CSV for external distribution
5. Revoke codes by clicking the "Revoke" button

#### Monitoring Usage
- View real-time usage statistics
- See which users have used each code
- Monitor expiration dates
- Track creation and last usage times

### For New Users

#### Registration Process
1. Obtain an invite code from an administrator
2. Navigate to `/register/` or click "Register with invite code" on login page
3. Enter the invite code (automatically formatted)
4. Fill in personal information (username, email, name)
5. Create a secure password
6. Click "Create Account"
7. You'll be automatically logged in and assigned to the appropriate role/task group

#### Mobile Registration
1. Use the `/api/register/` endpoint
2. Send POST request with registration data
3. Handle the response (success/error)
4. Store authentication tokens if successful

## 🔧 Configuration

### Settings
No additional settings required - the system uses existing Django settings.

### Permissions
- **Admin Access**: Only superusers can create and manage invite codes
- **Registration Access**: Public access to registration endpoints
- **API Access**: Public access to registration API (no authentication required)

### Customization
- **Code Length**: Modify `generate_invite_code()` function to change code length
- **Code Format**: Update alphabet in code generation for different formats
- **Expiration Defaults**: Modify admin form defaults
- **UI Styling**: Customize templates in `api/templates/registration/`

## 🚨 Troubleshooting

### Common Issues

#### "Invalid invite code" Error
- **Cause**: Code doesn't exist, expired, or already used
- **Solution**: Check code validity, create new code, or extend expiration

#### "Username already exists" Error
- **Cause**: Username is already taken
- **Solution**: Choose a different username

#### "Email already exists" Error
- **Cause**: Email is already registered
- **Solution**: Use a different email or reset password for existing account

#### Registration Form Not Loading
- **Cause**: URL routing issue
- **Solution**: Check that `/register/` is included in main URL configuration

### Debug Mode
Enable Django debug mode to see detailed error messages:
```python
DEBUG = True
```

### Logging
Check application logs for detailed error information:
```bash
tail -f logs/debug.log
```

## 📈 Performance Considerations

### Database Optimization
- **Indexes**: Code field is indexed for fast lookups
- **Queries**: Uses `select_related` for efficient admin queries
- **Pagination**: Admin interface supports pagination for large datasets

### Caching
- **Code Validation**: Consider caching frequently validated codes
- **Admin Lists**: Consider caching admin list views for better performance

### Scalability
- **Code Generation**: Uses efficient collision detection
- **Bulk Operations**: Admin supports bulk operations for large datasets
- **API Rate Limiting**: Consider adding rate limiting for registration API

## 🔄 Future Enhancements

### Planned Features
- **Email Notifications**: Send invite codes via email
- **Bulk Code Generation**: Generate multiple codes at once
- **Code Templates**: Pre-configured code templates for common roles
- **Analytics Dashboard**: Detailed usage analytics and reporting
- **Integration**: Integration with external identity providers

### Mobile App Integration
- **Push Notifications**: Notify users of new invite codes
- **QR Code Support**: Generate QR codes for easy sharing
- **Offline Support**: Cache invite codes for offline validation

## 📚 Related Documentation

- [API Documentation](../backend/API_DOCUMENTATION.md)
- [Admin Interface Guide](../backend/ADMIN_INTERFACE_GUIDE.md)
- [Security Implementation](../security/SECURITY_IMPLEMENTATION.md)
- [User Management](../backend/USER_MANAGEMENT.md)

## 🤝 Support

For technical support or questions about the registration system:
- Check the troubleshooting section above
- Review the test cases for usage examples
- Contact the development team for advanced configuration

---

**Last Updated:** September 11, 2025  
**Maintained By:** AriStay Development Team  
**Version:** 1.0
