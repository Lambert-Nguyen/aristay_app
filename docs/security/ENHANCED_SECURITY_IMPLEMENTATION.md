# 🛡️ Enhanced Security & Rate Limiting Implementation

## Overview
Comprehensive security enhancements for authentication and API protection.

## 1. Advanced Rate Limiting

### Install Dependencies
```bash
pip install django-ratelimit
pip install django-axes  # For login attempt monitoring
```

### Enhanced Settings
```python
# backend/settings.py
INSTALLED_APPS = [
    # ... existing apps
    'axes',
]

MIDDLEWARE = [
    # ... existing middleware
    'axes.middleware.AxesMiddleware',  # Add before auth middleware
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]

# Enhanced rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Axes configuration for login protection
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=30)
AXES_LOCKOUT_TEMPLATE = 'auth/account_locked.html'
AXES_RESET_ON_SUCCESS = True
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True

# Enhanced DRF rate limiting
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/minute',
        'password_reset': '3/hour',
        'token_refresh': '10/minute',
        'admin_api': '500/hour',
        'file_upload': '20/day',
    },
}
```

## 2. Custom Authentication Middleware

```python
# backend/middleware.py
class EnhancedAuthMiddleware:
    """Enhanced authentication middleware with security logging"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.security_logger = logging.getLogger('api.security')
    
    def __call__(self, request):
        # Pre-process security checks
        self._log_auth_attempt(request)
        self._check_suspicious_patterns(request)
        
        response = self.get_response(request)
        
        # Post-process security logging
        self._log_auth_result(request, response)
        
        return response
    
    def _log_auth_attempt(self, request):
        """Log authentication attempts"""
        if request.path in ['/api/token/', '/api-token-auth/', '/login/']:
            self.security_logger.info(
                f"Auth attempt from {self._get_client_ip(request)}",
                extra={
                    'security_event': 'auth_attempt',
                    'ip_address': self._get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'path': request.path,
                }
            )
    
    def _check_suspicious_patterns(self, request):
        """Check for suspicious request patterns"""
        ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check for common attack patterns
        suspicious_patterns = [
            'sqlmap', 'nikto', 'nmap', 'burp', 'owasp',
            'python-requests', 'curl', 'wget'  # Adjust based on legitimate usage
        ]
        
        if any(pattern in user_agent.lower() for pattern in suspicious_patterns):
            self.security_logger.warning(
                f"Suspicious user agent detected: {user_agent}",
                extra={
                    'security_event': 'suspicious_user_agent',
                    'ip_address': ip,
                    'user_agent': user_agent,
                }
            )
    
    def _get_client_ip(self, request):
        """Get client IP handling proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
```

## 3. Token Security Model

```python
# api/models.py
class UserSession(models.Model):
    """Track user sessions for enhanced security"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    device_type = models.CharField(max_length=50, default='unknown')
    location = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
        ]

class SecurityEvent(models.Model):
    """Log security events for monitoring"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium'
    )
    
    class Meta:
        db_table = 'security_events'
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
```

## 4. Enhanced API Security Views

```python
# api/security_views.py
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from ratelimit.decorators import ratelimit

@method_decorator([
    ratelimit(key='ip', rate='5/m', method='POST'),
    csrf_protect,
    never_cache,
], name='dispatch')
class SecureTokenObtainView(TokenObtainPairView):
    """Secure token obtain with enhanced logging and rate limiting"""
    
    def post(self, request, *args, **kwargs):
        # Log attempt
        self._log_auth_attempt(request)
        
        response = super().post(request, *args, **kwargs)
        
        # Log result
        self._log_auth_result(request, response)
        
        return response
    
    def _log_auth_attempt(self, request):
        SecurityEvent.objects.create(
            event_type='login_attempt',
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={
                'username': request.data.get('username'),
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    def _log_auth_result(self, request, response):
        success = response.status_code == 200
        
        if success:
            # Get user from response
            username = request.data.get('username')
            try:
                user = User.objects.get(username=username)
                self._create_session_record(request, user)
            except User.DoesNotExist:
                pass
        
        SecurityEvent.objects.create(
            event_type='login_result',
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            severity='low' if success else 'medium',
            details={
                'success': success,
                'status_code': response.status_code,
                'username': request.data.get('username'),
            }
        )
    
    def _create_session_record(self, request, user):
        """Create session record for tracking"""
        UserSession.objects.create(
            user=user,
            session_key=f"jwt_{timezone.now().timestamp()}",
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            device_type=self._detect_device_type(request),
        )
```

## 5. Mobile App Security Enhancement

```dart
// lib/services/secure_storage.dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:crypto/crypto.dart';

class SecureTokenStorage {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
    iOptions: IOSOptions(
      accessibility: IOSAccessibility.first_unlock_this_device,
    ),
  );
  
  static Future<void> storeTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _storage.write(key: 'access_token', value: accessToken);
    await _storage.write(key: 'refresh_token', value: refreshToken);
    await _storage.write(
      key: 'token_timestamp', 
      value: DateTime.now().millisecondsSinceEpoch.toString(),
    );
  }
  
  static Future<bool> isTokenValid() async {
    final timestamp = await _storage.read(key: 'token_timestamp');
    if (timestamp == null) return false;
    
    final tokenTime = DateTime.fromMillisecondsSinceEpoch(int.parse(timestamp));
    final now = DateTime.now();
    
    // Check if token is older than 55 minutes (5 minute buffer)
    return now.difference(tokenTime).inMinutes < 55;
  }
  
  static Future<void> clearTokens() async {
    await _storage.deleteAll();
  }
}
```

## 6. Security Monitoring Dashboard

```python
# api/security_dashboard.py
@login_required
@user_passes_test(lambda u: u.is_superuser)
def security_dashboard(request):
    """Security monitoring dashboard for admins"""
    
    # Get recent security events
    recent_events = SecurityEvent.objects.order_by('-created_at')[:100]
    
    # Get login statistics
    login_stats = {
        'successful_logins_24h': SecurityEvent.objects.filter(
            event_type='login_result',
            details__success=True,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count(),
        'failed_logins_24h': SecurityEvent.objects.filter(
            event_type='login_result',
            details__success=False,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count(),
    }
    
    # Get active sessions
    active_sessions = UserSession.objects.filter(
        is_active=True,
        last_activity__gte=timezone.now() - timedelta(hours=24)
    ).count()
    
    context = {
        'recent_events': recent_events,
        'login_stats': login_stats,
        'active_sessions': active_sessions,
    }
    
    return render(request, 'admin/security_dashboard.html', context)
```

## 7. Automated Security Alerts

```python
# api/security_alerts.py
def check_security_threats():
    """Check for security threats and send alerts"""
    
    # Check for brute force attempts
    failed_logins = SecurityEvent.objects.filter(
        event_type='login_result',
        details__success=False,
        created_at__gte=timezone.now() - timedelta(minutes=5)
    ).values('ip_address').annotate(count=Count('ip_address'))
    
    for item in failed_logins:
        if item['count'] > 10:  # More than 10 failures in 5 minutes
            send_security_alert(
                f"Potential brute force attack from {item['ip_address']}"
            )
    
    # Check for suspicious user agents
    suspicious_events = SecurityEvent.objects.filter(
        event_type='suspicious_user_agent',
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    if suspicious_events > 5:
        send_security_alert(f"High number of suspicious requests: {suspicious_events}")

def send_security_alert(message):
    """Send security alert to administrators"""
    # Send email or Slack notification
    pass
```

## Implementation Priority

1. **Phase 1 (High Priority)**: JWT implementation with refresh tokens
2. **Phase 2 (Medium Priority)**: Enhanced rate limiting and session tracking
3. **Phase 3 (Low Priority)**: Security monitoring dashboard and alerts

## Security Monitoring Checklist

- [ ] Failed login attempts > 5 per IP in 5 minutes
- [ ] Suspicious user agents or request patterns
- [ ] Token usage anomalies (location, device changes)
- [ ] Multiple concurrent sessions from different locations
- [ ] Admin permission changes or escalations
- [ ] Password reset request spikes
- [ ] API rate limit violations

## Performance Considerations

- Use Redis for session storage and rate limiting
- Index security event tables properly
- Implement log rotation for security events
- Consider archiving old security events
