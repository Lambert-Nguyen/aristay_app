# api/digest_views.py
"""
Email Digest Service DRF Views and Management UI
Provides DRF endpoints and HTML interface for email digest management
"""

import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers

from .decorators import staff_or_perm
from .services.email_digest_service import EmailDigestService
from .models import Profile

logger = logging.getLogger(__name__)


# DRF API Views
@extend_schema(
    operation_id="send_digest",
    summary="Trigger a digest send (admin/ops)",
    request=inline_serializer(
        name="SendDigestRequest",
        fields={
            "test_mode": serializers.BooleanField(required=False, default=False),
            "dry_run": serializers.BooleanField(required=False, default=False),
        },
    ),
    responses=inline_serializer(
        name="SendDigestResponse",
        fields={
            "success": serializers.BooleanField(),
            "sent_count": serializers.IntegerField(required=False),
            "message": serializers.CharField(required=False),
        },
    ),
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_digest_api(request):
    """
    DRF API endpoint to trigger email digest sending
    POST /api/digest/send/
    """
    if not request.user.is_staff:
        return Response(
            {"error": "Staff permissions required"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    test_mode = request.data.get('test_mode', False)
    
    try:
        if not settings.EMAIL_DIGEST_ENABLED:
            return Response({
                "success": False,
                "message": "Email digest is disabled in settings",
                "sent_count": 0
            })
        
        sent_count = EmailDigestService.send_daily_digest(test_mode=test_mode)
        
        return Response({
            "success": True,
            "message": f"Email digest sent to {sent_count} users" if not test_mode 
                      else f"Test mode: would send to {sent_count} users",
            "sent_count": sent_count,
            "test_mode": test_mode
        })
        
    except Exception as e:
        logger.error(f"Error sending email digest: {str(e)}")
        return Response({
            "success": False,
            "error": f"Failed to send digest: {str(e)}",
            "sent_count": 0
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    operation_id="digest_settings",
    summary="Get current digest settings",
    responses=inline_serializer(
        name="DigestSettingsResponse",
        fields={
            "global_enabled": serializers.BooleanField(),
            "user_opted_out": serializers.BooleanField(),
            "user_count": serializers.IntegerField(),
            "opted_out_count": serializers.IntegerField(),
            "opt_out_percentage": serializers.FloatField(),
        },
    ),
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def digest_settings_api(request):
    """
    DRF API endpoint to get digest settings and user opt-out status
    GET /api/digest/settings/
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    user_count = User.objects.count()
    opted_out_count = Profile.objects.filter(digest_opt_out=True).count()
    
    return Response({
        "global_enabled": getattr(settings, 'EMAIL_DIGEST_ENABLED', False),
        "user_opted_out": profile.digest_opt_out,
        "user_timezone": profile.timezone,
        "total_users": user_count,
        "opted_out_users": opted_out_count,
        "eligible_users": user_count - opted_out_count
    })


@extend_schema(
    operation_id="digest_opt_out",
    summary="Opt in/out of email digests",
    request=inline_serializer(
        name="DigestOptOutRequest",
        fields={
            "opted_out": serializers.BooleanField(),
            "reason": serializers.CharField(required=False),
        },
    ),
    responses=inline_serializer(
        name="DigestOptOutResponse",
        fields={"success": serializers.BooleanField(), "message": serializers.CharField()},
    ),
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def digest_opt_out_api(request):
    """
    DRF API endpoint to opt user in/out of email digest
    POST /api/digest/opt-out/ with {"opted_out": true/false}
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    opted_out = request.data.get('opted_out', False)
    
    profile.digest_opt_out = opted_out
    profile.save()
    
    return Response({
        "success": True,
        "opted_out": profile.digest_opt_out,
        "message": "Opted out of email digest" if opted_out else "Opted in to email digest"
    })


# HTML Management UI Views
@login_required
@staff_or_perm('can_manage_notifications')
def digest_management_view(request):
    """
    HTML interface for email digest management
    GET/POST /api/admin/digest-management/
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'send_digest':
            test_mode = request.POST.get('test_mode') == 'on'
            
            try:
                if not settings.EMAIL_DIGEST_ENABLED:
                    return JsonResponse({
                        "success": False,
                        "message": "Email digest is disabled in settings"
                    })
                
                sent_count = EmailDigestService.send_daily_digest(test_mode=test_mode)
                
                return JsonResponse({
                    "success": True,
                    "message": f"Email digest {'tested' if test_mode else 'sent'} for {sent_count} users",
                    "sent_count": sent_count
                })
                
            except Exception as e:
                logger.error(f"Error sending digest: {str(e)}")
                return JsonResponse({
                    "success": False,
                    "error": f"Failed to send digest: {str(e)}"
                })
    
    # GET request - show management interface
    user_count = User.objects.count()
    opted_out_count = Profile.objects.filter(digest_opt_out=True).count()
    eligible_users = user_count - opted_out_count
    
    context = {
        "global_enabled": getattr(settings, 'EMAIL_DIGEST_ENABLED', False),
        "total_users": user_count,
        "opted_out_users": opted_out_count,
        "eligible_users": eligible_users,
        "page_title": "Email Digest Management"
    }
    
    return render(request, 'admin/digest_management.html', context)


@login_required
def digest_settings_view(request):
    """
    User settings for email digest preferences
    GET/POST /api/digest/settings/
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        opted_out = request.POST.get('digest_opt_out') == 'on'
        profile.digest_opt_out = opted_out
        profile.save()
        
        return JsonResponse({
            "success": True,
            "message": "Digest preferences updated",
            "opted_out": opted_out
        })
    
    context = {
        "profile": profile,
        "global_enabled": getattr(settings, 'EMAIL_DIGEST_ENABLED', False),
        "page_title": "Email Digest Settings"
    }
    
    return render(request, 'portal/digest_settings.html', context)