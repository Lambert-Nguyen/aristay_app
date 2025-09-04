"""
Agent's Phase 2: API views for audit events with searchable fields and export
"""
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.utils import timezone
from django.db import models
import csv
from api.models import AuditEvent
from api.serializers import AuditEventSerializer


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Agent's Phase 2: Read-only API for audit events with field filters and export.
    
    Provides:
    - List view with filtering and search
    - Detail view for individual audit events
    - CSV export functionality
    """
    queryset = AuditEvent.objects.all()
    serializer_class = AuditEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Agent's recommendation: searchable audit log with field filters
    filterset_fields = {
        'object_type': ['exact', 'icontains'],
        'object_id': ['exact'],
        'action': ['exact'],
        'actor': ['exact'],
        'created_at': ['gte', 'lte', 'date'],
        'ip_address': ['exact'],
    }
    
    search_fields = [
        'object_type',
        'object_id', 
        'actor__username',
        'ip_address',
        'request_id',
    ]
    
    ordering_fields = ['created_at', 'action', 'object_type']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """Only authenticated users can view audit logs."""
        permission_classes = [permissions.IsAuthenticated]
        
        # Additional permission check for sensitive audit data
        if hasattr(self.request.user, 'is_staff') and not self.request.user.is_staff:
            # Non-staff users can only see their own actions, but still need IsAuthenticated
            pass
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # If user is not staff, only show their own audit events
        if not self.request.user.is_staff:
            queryset = queryset.filter(actor=self.request.user)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        Agent's recommendation: Export audit events to CSV.
        
        Query parameters:
        - All the same filters as list view
        - format: 'csv' (default)
        """
        # Apply the same filters as the list view
        queryset = self.filter_queryset(self.get_queryset())
        
        # Limit export size for performance
        if queryset.count() > 10000:
            return Response({
                'error': 'Export limited to 10,000 records. Please add filters to reduce the dataset.'
            }, status=400)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="audit_export_{timestamp}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Created At',
            'Action', 
            'Object Type',
            'Object ID',
            'Actor',
            'IP Address',
            'Request ID',
            'User Agent',
            'Changes'
        ])
        
        # Write data
        for event in queryset:
            writer.writerow([
                event.created_at.isoformat(),
                event.action,
                event.object_type,
                event.object_id,
                event.actor.username if event.actor else 'System',
                event.ip_address or '',
                event.request_id,
                event.user_agent,
                str(event.changes)
            ])
        
        return response
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get audit event summary statistics.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Basic counts
        total_events = queryset.count()
        
        # Action breakdown
        action_counts = {}
        for action, _ in AuditEvent.ACTION_CHOICES:
            action_counts[action] = queryset.filter(action=action).count()
        
        # Top object types
        object_type_counts = (
            queryset.values('object_type')
            .annotate(count=models.Count('id'))
            .order_by('-count')[:10]
        )
        
        # Top actors
        actor_counts = (
            queryset.filter(actor__isnull=False)
            .values('actor__username')
            .annotate(count=models.Count('id'))
            .order_by('-count')[:10]
        )
        
        return Response({
            'total_events': total_events,
            'action_breakdown': action_counts,
            'top_object_types': list(object_type_counts),
            'top_actors': list(actor_counts),
            'date_range': {
                'earliest': queryset.earliest('created_at').created_at if total_events > 0 else None,
                'latest': queryset.latest('created_at').created_at if total_events > 0 else None,
            }
        })
        
    @action(detail=True, methods=['get'])
    def related_events(self, request, pk=None):
        """
        Get related audit events for the same object.
        """
        event = self.get_object()
        
        # Find all events for the same object
        related = AuditEvent.objects.filter(
            object_type=event.object_type,
            object_id=event.object_id
        ).exclude(pk=event.pk).order_by('-created_at')
        
        serializer = self.get_serializer(related, many=True)
        return Response(serializer.data)
