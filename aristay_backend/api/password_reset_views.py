"""
Custom password reset views with audit logging
"""
import logging
from django.contrib.auth.views import (
    PasswordResetView as DjangoPasswordResetView,
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
    PasswordResetDoneView as DjangoPasswordResetDoneView,
    PasswordResetCompleteView as DjangoPasswordResetCompleteView
)
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from api.password_reset_logs import log_password_reset_event

logger = logging.getLogger(__name__)
User = get_user_model()


class PasswordResetView(DjangoPasswordResetView):
    """
    Custom password reset view that logs reset requests
    """
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    
    def form_valid(self, form):
        """Log password reset request"""
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
            logger.info(f"🔐 Password reset requested for user: {user.username} ({email})")
            
            # Log password reset request
            log_password_reset_event(user, 'requested', self.request, f"Email: {email}")
            
        except User.DoesNotExist:
            logger.warning(f"🔐 Password reset requested for non-existent email: {email}")
        
        return super().form_valid(form)


class PasswordResetConfirmView(DjangoPasswordResetConfirmView):
    """
    Custom password reset confirm view that logs successful resets
    """
    template_name = 'registration/password_reset_confirm.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('password_reset_complete')
    
    def form_valid(self, form):
        """Log successful password reset"""
        user = self.user
        if user:
            logger.info(f"🔐 Password successfully reset for user: {user.username}")
            
            # Log password reset success
            log_password_reset_event(user, 'completed', self.request, "Password successfully reset via email")
            
            # Also log to Django admin history via LogEntry
            self._log_to_admin_history(user)
        
        return super().form_valid(form)
    
    def _log_to_admin_history(self, user):
        """Log password reset to Django admin history"""
        try:
            from django.contrib.admin.models import LogEntry
            from django.contrib.contenttypes.models import ContentType
            
            # Create a LogEntry for the password reset
            content_type = ContentType.objects.get_for_model(user)
            
            LogEntry.objects.log_action(
                user_id=user.id,  # The user who reset their password
                content_type_id=content_type.id,
                object_id=user.id,
                object_repr=str(user),
                action_flag=LogEntry.CHANGE,
                change_message="Password reset via email"
            )
            
            logger.info(f"📝 Logged password reset to admin history for {user.username}")
            
        except Exception as e:
            logger.error(f"❌ Failed to log password reset to admin history for {user.username}: {e}")


class PasswordResetDoneView(DjangoPasswordResetDoneView):
    """Custom password reset done view"""
    template_name = 'registration/password_reset_done.html'


class PasswordResetCompleteView(DjangoPasswordResetCompleteView):
    """Custom password reset complete view"""
    template_name = 'registration/password_reset_complete.html'
