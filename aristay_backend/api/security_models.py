# api/security_models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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
    jwt_jti = models.CharField(max_length=255, blank=True)  # JWT Token ID
    
    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
            models.Index(fields=['jwt_jti']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type} ({self.ip_address})"
    
    def deactivate(self):
        """Deactivate session"""
        self.is_active = False
        self.save()
    
    @property
    def is_expired(self):
        """Check if session is expired (24 hours of inactivity)"""
        from datetime import timedelta
        return timezone.now() - self.last_activity > timedelta(hours=24)

class SecurityEvent(models.Model):
    """Log security events for monitoring"""
    
    EVENT_TYPES = [
        ('login_attempt', 'Login Attempt'),
        ('login_success', 'Login Success'),
        ('login_failure', 'Login Failure'),
        ('token_issued', 'Token Issued'),
        ('token_refreshed', 'Token Refreshed'),
        ('token_revoked', 'Token Revoked'),
        ('password_reset', 'Password Reset'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('permission_denied', 'Permission Denied'),
        ('account_locked', 'Account Locked'),
        ('session_expired', 'Session Expired'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='medium')
    resolved = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'security_events'
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['severity', 'resolved']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.severity} - {self.created_at}"
    
    @classmethod
    def log_event(cls, event_type, request=None, user=None, severity='medium', **kwargs):
        """Convenience method to log security events"""
        ip_address = '127.0.0.1'
        user_agent = ''
        
        if request:
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            if not user and hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
        
        return cls.objects.create(
            user=user,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
            details=kwargs
        )
    
    @staticmethod
    def _get_client_ip(request):
        """Get client IP handling proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

class SuspiciousActivity(models.Model):
    """Track patterns of suspicious activity"""
    ip_address = models.GenericIPAddressField(db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    activity_type = models.CharField(max_length=50)
    count = models.IntegerField(default=1)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    blocked = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'suspicious_activity'
        unique_together = ['ip_address', 'activity_type']
        indexes = [
            models.Index(fields=['ip_address', 'blocked']),
            models.Index(fields=['activity_type', 'count']),
        ]
    
    def increment(self):
        """Increment activity count"""
        self.count += 1
        self.last_seen = timezone.now()
        self.save()
    
    def should_block(self):
        """Determine if this activity should be blocked"""
        thresholds = {
            'failed_login': 10,
            'rate_limit_exceeded': 5,
            'suspicious_user_agent': 3,
            'invalid_token': 15,
        }
        
        threshold = thresholds.get(self.activity_type, 20)
        return self.count >= threshold
