# 📊 AriStay Backend Logging System

## 🚀 **Production-Ready Logging & Monitoring**

This document describes the comprehensive logging and monitoring system implemented for the AriStay backend, designed for production environments with proper error tracking, performance monitoring, and security logging.

---

## 📋 **Overview**

The logging system provides:

- **📝 Structured JSON Logging** - Machine-readable logs for monitoring tools
- **🔄 Automatic Log Rotation** - Prevents disk space issues
- **🎯 Multiple Log Levels** - Separate files for different log types
- **⚡ Performance Monitoring** - Request/response timing and database metrics
- **🛡️ Security Logging** - Authentication attempts and suspicious activity
- **🚨 Error Tracking** - Integration with Sentry for real-time alerts
- **💊 Health Checks** - Monitoring endpoints for load balancers

---

## 📁 **Log Files Structure**

```
logs/
├── debug.log           # Debug-level logs (development only)
├── info.log            # General application logs
├── error.log           # Error and exception logs
├── security.log        # Security-related events
├── performance.log     # Request timing and performance metrics
├── digest.log          # Email digest system logs
└── digest_err.log      # Email digest error logs
```

### **Log Rotation Settings**

- **Info logs**: 100MB files, 10 backups
- **Error logs**: 50MB files, 20 backups (kept longer)
- **Debug logs**: 50MB files, 5 backups (development only)
- **Security logs**: 25MB files, 15 backups
- **Performance logs**: 100MB files, 7 backups (weekly rotation)

---

## 🏗️ **System Architecture**

### **Middleware Components**

1. **RequestLoggingMiddleware** - Logs all HTTP requests with performance metrics
2. **ErrorLoggingMiddleware** - Captures unhandled exceptions
3. **SecurityHeadersMiddleware** - Adds security headers and logs security events

### **Log Formatters**

1. **JSONFormatter** - Standard structured logging
2. **SecurityFormatter** - Security-specific logs with data sanitization
3. **PerformanceFormatter** - Performance metrics and timing data

---

## 📊 **JSON Log Format**

Each log entry includes:

```json
{
  "timestamp": "2025-08-28T00:13:17.982469Z",
  "level": "INFO",
  "logger": "api",
  "message": "User login successful",
  "module": "views",
  "function": "login",
  "line": 123,
  "process": 90225,
  "thread": 8795562176,
  "thread_name": "MainThread",
  "environment": {
    "debug": false,
    "service": "aristay-backend",
    "version": "1.0.0"
  },
  "request": {
    "method": "POST",
    "path": "/api/auth/login/",
    "user_id": 42,
    "user_agent": "Mozilla/5.0...",
    "remote_addr": "192.168.1.100"
  },
  "performance": {
    "duration_ms": 245,
    "slow_query": false
  }
}
```

---

## 🎯 **Log Categories**

### **Performance Logs** (`api.performance`)
- Request/response timing
- Database query metrics
- Memory usage tracking
- Slow operation alerts

```python
logger = logging.getLogger('api.performance')
logger.info('Slow request detected', extra={
    'duration': 1500,
    'queries_count': 25,
    'memory_usage': 150.5
})
```

### **Security Logs** (`api.security`)
- Authentication attempts
- Admin access
- Suspicious patterns
- Failed authorization

```python
logger = logging.getLogger('api.security')
logger.warning('Failed login attempt', extra={
    'security_event': 'failed_login',
    'security_category': 'authentication',
    'attempt_count': 3
})
```

### **Application Logs** (`api`)
- Business logic events
- Task operations
- User actions
- System state changes

```python
logger = logging.getLogger('api')
logger.info('Task created successfully', extra={
    'task_id': 123,
    'user_id': 42,
    'property_id': 10
})
```

---

## 🚨 **Sentry Integration**

### **Setup**
Set environment variable:
```bash
export SENTRY_DSN="https://your-sentry-dsn@sentry.io/project-id"
```

### **Features**
- **Real-time error alerts**
- **Performance monitoring**
- **Release tracking**
- **User context**
- **Request context**
- **Custom tags and filtering**

### **Usage in Code**
```python
from backend.sentry_config import add_user_context, capture_task_context

# Add user context
add_user_context(request.user)

# Add task context for background jobs
capture_task_context('send_email_digest', task_args=[user_id])
```

---

## 🏥 **Health Check Endpoints**

### **Basic Health Check** - `/api/health/`
- **Purpose**: Load balancer health checks
- **Response**: Simple OK/FAIL status
- **Authentication**: None required

```bash
curl http://localhost:8000/api/health/
```

```json
{
  "status": "healthy",
  "timestamp": "2025-08-28T00:13:17Z",
  "service": "aristay-backend",
  "version": "1.0.0"
}
```

### **Detailed Health Check** - `/api/health/detailed/`
- **Purpose**: Administrator monitoring
- **Response**: Comprehensive system metrics
- **Authentication**: Staff required

```json
{
  "status": "healthy",
  "checks": {
    "database": {"healthy": true, "duration_ms": 12},
    "cache": {"healthy": true, "duration_ms": 3},
    "filesystem": {"healthy": true, "disk_free_percent": 45.2}
  },
  "metrics": {
    "system": {
      "cpu": {"usage_percent": 15.2},
      "memory": {"usage_percent": 68.4}
    },
    "application": {
      "tasks": {"total": 1250, "overdue": 5},
      "users": {"total": 45, "active_24h": 23}
    }
  }
}
```

---

## ⚙️ **Configuration**

### **Environment Variables**

```bash
# Core settings
DJANGO_ENVIRONMENT=production
DEBUG=False
APP_VERSION=1.0.0

# Sentry
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1

# Performance thresholds
SLOW_REQUEST_THRESHOLD=1000   # milliseconds
SLOW_QUERY_THRESHOLD=100      # milliseconds

# Admin notifications
DJANGO_ADMINS=Admin:admin@example.com,Tech:tech@example.com
```

### **Production Security Settings**

When `DEBUG=False`, the system automatically enables:

- **HTTPS redirects**
- **Security headers** (HSTS, Content-Type-Options, XSS-Protection)
- **Secure cookies**
- **CORS restrictions**
- **Database connection pooling**

---

## 📈 **Monitoring Integration**

### **Log Aggregation**
The JSON format works with popular log aggregation tools:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Fluentd**
- **Splunk**
- **DataDog**
- **CloudWatch Logs**

### **Metrics Collection**
Health check endpoints can be integrated with:
- **Prometheus** + **Grafana**
- **New Relic**
- **DataDog**
- **AWS CloudWatch**

---

## 🚀 **Production Deployment**

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Set Environment Variables**
```bash
cp env.production.example .env
# Edit .env with your production values
```

### **3. Configure Sentry**
```bash
export SENTRY_DSN="your-sentry-dsn"
```

### **4. Set Up Log Rotation** (systemd example)
```bash
# Create logrotate configuration
sudo cat > /etc/logrotate.d/aristay << EOF
/var/log/aristay/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    copytruncate
    sharedscripts
}
EOF
```

### **5. Configure Monitoring**
- Set up **Sentry project**
- Configure **health check monitoring**
- Set up **log aggregation**
- Configure **alerting rules**

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Log Files Not Created**
```bash
# Check directory permissions
ls -la logs/
chmod 755 logs/

# Check Django settings
python manage.py check
```

#### **Sentry Not Working**
```bash
# Test Sentry connection
python manage.py shell -c "
import sentry_sdk
sentry_sdk.capture_message('Test message')
"
```

#### **High Log Volume**
```bash
# Check log file sizes
du -sh logs/*.log

# Adjust log levels in settings
# Change DEBUG logs to INFO in production
```

### **Performance Issues**

#### **Slow Requests**
Monitor `performance.log` for:
- Requests > 1000ms
- Database queries > 100ms
- High memory usage

#### **Database Performance**
Check detailed health endpoint:
```bash
curl -H "Authorization: Bearer your-token" \
     http://localhost:8000/api/health/detailed/
```

---

## 📚 **Best Practices**

### **1. Log Levels**
- **DEBUG**: Development debugging only
- **INFO**: Normal application flow
- **WARNING**: Unusual but handled situations
- **ERROR**: Error conditions that need attention
- **CRITICAL**: Serious errors that may abort

### **2. Structured Data**
Always use the `extra` parameter for structured data:
```python
logger.info('User action', extra={
    'action': 'create_task',
    'user_id': request.user.id,
    'task_data': {'title': 'New task', 'priority': 'high'}
})
```

### **3. Security**
- Never log passwords or tokens
- Sanitize sensitive data automatically
- Use security logger for auth events

### **4. Performance**
- Monitor slow requests (>1s)
- Track database query counts
- Alert on memory usage spikes

---

## 🎯 **Next Steps**

### **Immediate (Production)**
1. ✅ Set up Sentry project
2. ✅ Configure environment variables
3. ✅ Set up log rotation
4. ✅ Configure health check monitoring

### **Enhanced Monitoring**
1. **Set up Prometheus metrics**
2. **Configure Grafana dashboards**
3. **Implement custom alerts**
4. **Add business metrics**

### **Advanced Features**
1. **Distributed tracing**
2. **Custom error pages**
3. **Rate limiting logs**
4. **Audit trail system**

---

## 🏆 **Summary**

The AriStay logging system provides enterprise-grade monitoring with:

- ✅ **Production-ready** structured logging
- ✅ **Automatic rotation** and space management
- ✅ **Real-time error tracking** with Sentry
- ✅ **Performance monitoring** with detailed metrics
- ✅ **Security logging** for compliance
- ✅ **Health checks** for monitoring integration
- ✅ **Easy configuration** with environment variables

Your backend is now ready for production deployment with comprehensive monitoring and alerting! 🚀

---

## 🆕 **Recent Updates & Fixes**

### **Version: Enhanced Logging System (Latest)**

#### **🔧 Critical Bug Fixes**

**1. Password Reset System Logging**
- ✅ **Admin Template Errors**: Fixed `NoReverseMatch: 'app_list'` errors in password change forms
- ✅ **URL Namespace Resolution**: Corrected manager admin namespace logging
- ✅ **Template Context Issues**: Fixed password reset button context logging
- ✅ **Permission Boundary Logging**: Enhanced role-based access logging

**2. Admin Site URL Pattern Logging**
- ✅ **Namespace Conflict Resolution**: Fixed `NoReverseMatch` errors with proper namespace logging
- ✅ **Custom Admin Class Logging**: Added logging for `AriStayUserAdmin` and `UserManagerAdmin`
- ✅ **URL Pattern Consistency**: Standardized URL logging across admin sites
- ✅ **Template Rendering Logs**: Enhanced template error logging and debugging

**3. Enhanced Security Event Logging**
- ✅ **Password Operation Audit**: All password changes and resets logged with user attribution
- ✅ **Permission Violation Logging**: Unauthorized access attempts tracked
- ✅ **Session Security Logging**: Enhanced authentication event logging
- ✅ **Form Validation Logging**: Role-based form restriction logging

#### **📊 New Log Categories Added**

```json
{
  "timestamp": "2025-08-30T01:27:56.000Z",
  "level": "INFO",
  "logger": "api.admin",
  "message": "Password reset email sent to user@example.com by admin",
  "user_id": 1,
  "target_user_id": 2,
  "ip_address": "127.0.0.1",
  "user_agent": "Mozilla/5.0..."
}
```

```json
{
  "timestamp": "2025-08-30T01:27:56.000Z",
  "level": "WARNING",
  "logger": "api.admin",
  "message": "Permission denied: Manager attempted direct password change",
  "user_id": 3,
  "user_role": "manager",
  "attempted_action": "password_change",
  "ip_address": "127.0.0.1"
}
```

#### **🎯 Log Analysis Commands**

**Password Management Logs**:
```bash
# View password reset operations
grep "password.*reset" logs/security.log

# Check permission violations
grep "Permission denied" logs/error.log

# Monitor admin operations
grep "admin.*password" logs/info.log
```

**URL Resolution Logs**:
```bash
# Check namespace resolution
grep "NoReverseMatch" logs/error.log

# Monitor URL pattern usage
grep "reverse.*admin" logs/debug.log
```

---

## 📞 **Support & Troubleshooting**

### **Common Issues & Solutions**

**1. NoReverseMatch Errors**
```bash
# Check namespace configuration
grep "namespace.*manager" logs/debug.log

# Verify URL patterns
python manage.py show_urls | grep "admin"
```

**2. Permission Errors**
```bash
# Check role assignments
grep "role.*manager" logs/info.log

# Monitor access attempts
grep "Permission denied" logs/security.log
```

**3. Template Errors**
```bash
# Check template rendering
grep "template.*error" logs/error.log

# Verify template context
grep "password_reset_url" logs/debug.log
```

For logging issues or configuration questions:
- Check log file permissions and disk space
- Verify log directory exists and is writable
- Ensure all required Python packages are installed
- Test logging configuration with management commands
- Review recent error logs for pattern analysis

---

## 📋 **Change Log**

### **Version History**
- **Initial Release**: Basic logging system with file rotation
- **Enhanced Release**: Advanced middleware and performance monitoring
- **Latest Update**: Password reset logging, admin fixes, security enhancements

### **Migration Status**
- ✅ **All logging configurations**: Active and functional
- ✅ **Log file rotation**: Working correctly
- ✅ **Error tracking**: Integrated and operational
- ✅ **Security logging**: Enhanced with password operations

---

*Last updated: August 2025 - Enhanced logging system with password management and admin fixes*
