# 🔐 JWT Authentication & Security System Documentation

## Overview

This document describes the comprehensive JWT authentication and security system implemented for the Aristay backend application.

## System Architecture

### Core Components

1. **JWT Authentication Views** (`api/auth_views.py`)
   - Custom token generation with enhanced claims
   - Token refresh with ownership verification
   - Token revocation (single and bulk)
   - Throttled endpoints for security

2. **Security Models** (`api/security_models.py`)
   - `UserSession` - Track active user sessions
   - `SecurityEvent` - Log all security-related events
   - `SuspiciousActivity` - Monitor and block suspicious behavior

3. **Security Dashboard** (`api/security_dashboard.py`)
   - Real-time monitoring of security events
   - Session management for administrators
   - Analytics and threat detection

4. **Enhanced Middleware** (`api/enhanced_security_middleware.py`)
   - Request/response security logging
   - Suspicious activity detection
   - Security headers injection

## Authentication Flow

### 1. Token Generation

```http
POST /api/token/
Content-Type: application/json

{
    "username": "user@example.com",
    "password": "secure_password"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1Q...",
    "refresh": "eyJ0eXAiOiJKV1Q...",
    "user": {
        "id": 1,
        "username": "user@example.com",
        "email": "user@example.com",
        "is_staff": false,
        "is_superuser": false
    }
}
```

### 2. Token Usage

Include the access token in the Authorization header:

```http
Authorization: Bearer eyJ0eXAiOiJKV1Q...
```

### 3. Token Refresh

```http
POST /api/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1Q..."
}
```

### 4. Token Revocation

**Single Token:**
```http
POST /api/token/revoke/
Authorization: Bearer eyJ0eXAiOiJKV1Q...
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1Q..."
}
```

**All Tokens:**
```http
POST /api/token/revoke-all/
Authorization: Bearer eyJ0eXAiOiJKV1Q...
```

## Security Features

### 1. Rate Limiting

- **Login attempts**: 5/minute
- **Token refresh**: 2/minute (reduced from 10/minute for security)
- **Password reset**: 3/hour
- **API calls**: 1000/hour per user

### 2. Token Security

- **Access token lifetime**: 30 minutes (reduced for security)
- **Refresh token lifetime**: 7 days
- **Token rotation**: Enabled
- **Blacklisting**: Enabled
- **Ownership verification**: Tokens can only be revoked by their owners

### 3. Security Monitoring

- All authentication events logged
- Suspicious activity detection
- Automatic IP blocking for repeated violations
- Real-time security dashboard for administrators

### 4. Enhanced Security Headers

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security: max-age=31536000`
- Custom CSP policy
- Permissions-Policy restrictions

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/token/` | Generate JWT tokens | No |
| POST | `/api/token/refresh/` | Refresh access token | No |
| POST | `/api/token/verify/` | Verify token validity | No |
| POST | `/api/token/revoke/` | Revoke single token | Yes |
| POST | `/api/token/revoke-all/` | Revoke all user tokens | Yes |
| GET | `/api/test-auth/` | Test authentication | Yes |

### Security Dashboard (Admin Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/security/` | Security dashboard |
| GET | `/api/admin/security/events/` | Security events API |
| GET | `/api/admin/security/sessions/` | Active sessions |
| POST | `/api/admin/security/sessions/<id>/terminate/` | Terminate session |
| GET | `/api/admin/security/analytics/` | Security analytics |

## Configuration

### Django Settings

```python
# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'SIGNING_KEY': os.getenv('JWT_SIGNING_KEY', SECRET_KEY),
    # ... other settings
}

# Rate Limiting
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'login': '5/minute',
        'token_refresh': '2/minute',
        'password_reset': '3/hour',
        # ... other rates
    }
}

# Security (django-axes)
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=30)
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]
```

### Environment Variables

Required environment variables for production:

```bash
# Separate JWT signing key for security
JWT_SIGNING_KEY=your_jwt_signing_key_here

# Email configuration
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your_email@domain.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Database (production)
DATABASE_URL=your_database_url
```

## Security Best Practices

### 1. Token Management
- Use separate signing key for JWT tokens
- Keep access token lifetime short (30 minutes)
- Implement proper token rotation
- Always verify token ownership before revocation

### 2. Rate Limiting
- Implement aggressive rate limiting on auth endpoints
- Monitor and adjust limits based on usage patterns
- Use different limits for different endpoint types

### 3. Monitoring
- Log all security events
- Implement real-time alerting for suspicious activity
- Regular security audit through dashboard
- Monitor failed login patterns

### 4. Production Hardening
- Use HTTPS in production
- Implement proper CSRF protection
- Set secure security headers
- Regular security updates

## Testing

### Smoke Test Script

Use the improved smoke test script to validate the system:

```bash
export USER_NAME=your_username
export USER_PASS=your_password
./jwt_smoke_test_improved.sh
```

### Unit Tests

Run the comprehensive test suite:

```bash
cd tests/security
python test_jwt_authentication.py
```

## Troubleshooting

### Common Issues

1. **Token Ownership Error (403)**
   - Ensure the refresh token belongs to the authenticated user
   - Check token hasn't been tampered with

2. **Rate Limiting (429)**
   - Wait for the cooldown period
   - Check rate limit settings in Django settings

3. **Invalid Token (401)**
   - Token may be expired or revoked
   - Generate new tokens through login

4. **AXES Account Locked**
   - Wait for cooldown period (30 minutes by default)
   - Or manually unlock through Django admin

### Debug Endpoints

- `/api/test-auth/` - Test JWT authentication
- Check Django logs for detailed error information
- Use security dashboard for monitoring

## Migration from Legacy Auth

If migrating from Django's token authentication:

1. Update client code to use JWT format
2. Handle token expiration and refresh logic
3. Update API endpoints to use JWT authentication
4. Test thoroughly with the smoke test script

## Security Considerations

- Never log JWT tokens in production
- Rotate JWT signing key regularly
- Monitor for security events actively
- Implement IP allowlisting for admin endpoints
- Regular security audits and penetration testing
