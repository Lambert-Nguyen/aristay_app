# Registration API Documentation - AriStay

**API Version:** 1.0  
**Last Updated:** September 11, 2025  
**Base URL:** `https://your-domain.com/api/`

## Overview

The AriStay Registration API provides endpoints for user registration with invite code validation. This API supports both web and mobile applications with comprehensive validation and error handling.

## Authentication

**Note:** Registration endpoints do not require authentication. Users are automatically logged in after successful registration.

## Endpoints

### 1. User Registration

#### POST /api/register/

Creates a new user account with invite code validation.

**Request:**
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

**Request Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Unique username (3-150 characters) |
| `email` | string | Yes | Valid email address |
| `password` | string | Yes | Password (minimum 8 characters) |
| `password_confirm` | string | Yes | Password confirmation (must match password) |
| `first_name` | string | No | User's first name (max 30 characters) |
| `last_name` | string | No | User's last name (max 30 characters) |
| `invite_code` | string | Yes | Valid invite code (8 characters) |

**Success Response (201 Created):**
```json
{
  "success": true,
  "user_id": 123,
  "username": "newuser",
  "role": "member",
  "task_group": "cleaning"
}
```

**Error Responses:**

**400 Bad Request - Invalid Data:**
```json
{
  "username": ["Username already exists"],
  "email": ["Email already exists"],
  "password": ["Passwords do not match"]
}
```

**400 Bad Request - Invalid Invite Code:**
```json
{
  "error": "Invalid invite code"
}
```

**400 Bad Request - Code Not Usable:**
```json
{
  "error": "Invite code is not usable"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Registration failed"
}
```

### 2. Invite Code Validation

#### POST /api/validate-invite/

Validates an invite code without creating a user account.

**Request:**
```http
POST /api/validate-invite/
Content-Type: application/json

{
  "code": "ABC12345"
}
```

**Request Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Invite code to validate (8 characters) |

**Success Response (200 OK):**
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

**Error Response (200 OK - Invalid Code):**
```json
{
  "valid": false,
  "error": "Invalid invite code"
}
```

**Error Response (200 OK - Code Not Usable):**
```json
{
  "valid": false,
  "error": "Code is not usable"
}
```

## Data Models

### User Registration Request
```typescript
interface UserRegistrationRequest {
  username: string;           // 3-150 characters, unique
  email: string;             // Valid email format, unique
  password: string;          // Minimum 8 characters
  password_confirm: string;  // Must match password
  first_name?: string;       // Optional, max 30 characters
  last_name?: string;        // Optional, max 30 characters
  invite_code: string;       // 8-character alphanumeric code
}
```

### User Registration Response
```typescript
interface UserRegistrationResponse {
  success: boolean;
  user_id: number;
  username: string;
  role: 'member' | 'manager' | 'admin';
  task_group: 'general' | 'cleaning' | 'maintenance' | 'laundry' | 'lawn_pool' | 'none';
}
```

### Invite Code Validation Request
```typescript
interface InviteCodeValidationRequest {
  code: string;  // 8-character alphanumeric code
}
```

### Invite Code Validation Response
```typescript
interface InviteCodeValidationResponse {
  valid: boolean;
  role?: 'member' | 'manager' | 'admin';
  task_group?: 'general' | 'cleaning' | 'maintenance' | 'laundry' | 'lawn_pool' | 'none';
  expires_at?: string;  // ISO 8601 datetime
  max_uses?: number;    // 0 = unlimited
  used_count?: number;
  error?: string;
}
```

## Error Handling

### HTTP Status Codes
- **200 OK**: Successful validation (even for invalid codes)
- **201 Created**: Successful user registration
- **400 Bad Request**: Invalid request data or invite code
- **500 Internal Server Error**: Server error during registration

### Error Response Format
```typescript
interface ErrorResponse {
  // Field validation errors
  [field_name: string]: string[];
  
  // General errors
  error?: string;
  
  // Non-field errors
  non_field_errors?: string[];
}
```

### Common Error Messages

#### Validation Errors
- `"Username already exists"`
- `"Email already exists"`
- `"Passwords do not match"`
- `"This field is required"`
- `"Ensure this field has at least 8 characters"`
- `"Enter a valid email address"`

#### Invite Code Errors
- `"Invalid invite code"`
- `"Invite code is not usable"`
- `"Code is not usable"`

#### System Errors
- `"Registration failed"`
- `"Server error"`

## Rate Limiting

**Note:** Registration endpoints are not currently rate-limited, but this may be implemented in future versions.

## Security Considerations

### Input Validation
- All inputs are validated on the server side
- Username and email uniqueness is enforced
- Password requirements are enforced (minimum 8 characters)
- Invite codes are validated for existence and usability

### Data Protection
- Passwords are hashed using Django's built-in password hashing
- Sensitive data is not logged
- All requests are logged for audit purposes

### Invite Code Security
- Codes are generated using cryptographically secure random generation
- Codes are case-sensitive and alphanumeric only
- Codes can be set to expire
- Usage limits can be enforced

## Examples

### JavaScript/Fetch Example
```javascript
// Register a new user
async function registerUser(userData) {
  try {
    const response = await fetch('/api/register/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData)
    });
    
    const data = await response.json();
    
    if (response.ok) {
      console.log('Registration successful:', data);
      return data;
    } else {
      console.error('Registration failed:', data);
      throw new Error(data.error || 'Registration failed');
    }
  } catch (error) {
    console.error('Network error:', error);
    throw error;
  }
}

// Validate invite code
async function validateInviteCode(code) {
  try {
    const response = await fetch('/api/validate-invite/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ code })
    });
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Validation error:', error);
    throw error;
  }
}

// Usage example
const userData = {
  username: 'newuser',
  email: 'user@example.com',
  password: 'securepass123',
  password_confirm: 'securepass123',
  first_name: 'John',
  last_name: 'Doe',
  invite_code: 'ABC12345'
};

// First validate the invite code
const validation = await validateInviteCode(userData.invite_code);
if (validation.valid) {
  console.log('Code is valid for role:', validation.role);
  // Proceed with registration
  const result = await registerUser(userData);
  console.log('User registered:', result);
} else {
  console.error('Invalid invite code:', validation.error);
}
```

### Python/Requests Example
```python
import requests
import json

# Register a new user
def register_user(user_data):
    url = 'https://your-domain.com/api/register/'
    
    try:
        response = requests.post(url, json=user_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_data = response.json()
        raise Exception(f"Registration failed: {error_data}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {e}")

# Validate invite code
def validate_invite_code(code):
    url = 'https://your-domain.com/api/validate-invite/'
    
    try:
        response = requests.post(url, json={'code': code})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Validation error: {e}")

# Usage example
user_data = {
    'username': 'newuser',
    'email': 'user@example.com',
    'password': 'securepass123',
    'password_confirm': 'securepass123',
    'first_name': 'John',
    'last_name': 'Doe',
    'invite_code': 'ABC12345'
}

# First validate the invite code
validation = validate_invite_code(user_data['invite_code'])
if validation['valid']:
    print(f"Code is valid for role: {validation['role']}")
    # Proceed with registration
    result = register_user(user_data)
    print(f"User registered: {result}")
else:
    print(f"Invalid invite code: {validation['error']}")
```

### cURL Examples
```bash
# Validate invite code
curl -X POST https://your-domain.com/api/validate-invite/ \
  -H "Content-Type: application/json" \
  -d '{"code": "ABC12345"}'

# Register user
curl -X POST https://your-domain.com/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "securepass123",
    "password_confirm": "securepass123",
    "first_name": "John",
    "last_name": "Doe",
    "invite_code": "ABC12345"
  }'
```

## Testing

### Test Endpoints
Use the following test data for development and testing:

**Valid Test Invite Code:** `TEST1234` (if created in admin)
**Test User Data:**
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "testpass123",
  "password_confirm": "testpass123",
  "first_name": "Test",
  "last_name": "User",
  "invite_code": "TEST1234"
}
```

### Postman Collection
Import the following Postman collection for API testing:

```json
{
  "info": {
    "name": "AriStay Registration API",
    "description": "API endpoints for user registration with invite codes"
  },
  "item": [
    {
      "name": "Validate Invite Code",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"code\": \"ABC12345\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/validate-invite/",
          "host": ["{{base_url}}"],
          "path": ["api", "validate-invite", ""]
        }
      }
    },
    {
      "name": "Register User",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"username\": \"newuser\",\n  \"email\": \"user@example.com\",\n  \"password\": \"securepass123\",\n  \"password_confirm\": \"securepass123\",\n  \"first_name\": \"John\",\n  \"last_name\": \"Doe\",\n  \"invite_code\": \"ABC12345\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/register/",
          "host": ["{{base_url}}"],
          "path": ["api", "register", ""]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "https://your-domain.com"
    }
  ]
}
```

## Changelog

### Version 1.0 (September 11, 2025)
- Initial release
- User registration with invite code validation
- Invite code validation endpoint
- Comprehensive error handling
- Full API documentation

## Support

For technical support or questions about the Registration API:
- Check the error messages and status codes
- Review the request/response examples
- Contact the development team for advanced issues

---

**API Documentation maintained by:** AriStay Development Team  
**Last Updated:** September 11, 2025  
**Version:** 1.0
