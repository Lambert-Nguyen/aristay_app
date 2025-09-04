"""
Agent's Phase 2: API views for audit events with searchable fields and export
Fixed per GPT agent: proper pagination, filtering, and test compatibility
"""
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.utils import timezone
import csv
from api.models import AuditEvent
from api.serializers import AuditEventSerializer


class DefaultPagination(PageNumberPagination):
    page_size = 10


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Agent's Phase 2: Read-only API for audit events with field filters and export.
    
    Provides:
    - List view with filtering and search
    - Detail view for individual audit events
    - CSV export functionality
    """
    queryset = AuditEvent.objects.all().select_related("actor").order_by("-created_at")
    serializer_class = AuditEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["object_type", "action", "actor"]
    search_fields = ["object_type", "action", "actor__username", "request_id", "ip_address", "user_agent"]
    ordering_fields = ["created_at", "action", "object_type"]
    pagination_class = DefaultPagination

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        qs = super().get_queryset()
        user = self.request.user
        if not getattr(user, "is_staff", False):
            return qs.filter(actor=user)
        return qs

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Summary statistics for audit events."""
        qs = self.filter_queryset(self.get_queryset())
        total = qs.count()
        action_breakdown = {k: qs.filter(action=k).count() for k in ["create", "update", "delete"]}
        top_object_types = list(qs.values_list("object_type", flat=True).distinct()[:10])
        top_actors = list(qs.values_list("actor", flat=True).distinct()[:10])
        return Response(
            {
                "total_events": total,
                "action_breakdown": action_breakdown,
                "top_object_types": top_object_types,
                "top_actors": top_actors,
            }
        )

    @action(detail=False, methods=["get"])
    def export(self, request):
        """Export audit events to CSV."""
        qs = self.filter_queryset(self.get_queryset()).order_by("-created_at")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="audit_events.csv"'
        writer = csv.writer(response)
        writer.writerow(
            ["Created At", "Action", "Object Type", "Object ID", "Actor", "Request ID", "IP Address", "User Agent", "Changes"]
        )
        for ev in qs:
            writer.writerow(
                [
                    ev.created_at.isoformat(),
                    ev.action,
                    ev.object_type,
                    ev.object_id,
                    ev.actor_id or "",
                    ev.request_id or "",
                    ev.ip_address or "",
                    ev.user_agent or "",
                    ev.changes,
                ]
            )
        return response

    @action(detail=True, methods=["get"])
    def related_events(self, request, pk=None):
        """Find related audit events for the same object."""
        ev = self.get_object()
        related = (
            AuditEvent.objects.filter(object_type=ev.object_type, object_id=ev.object_id)
            .exclude(pk=ev.pk)
            .order_by("-created_at")[:50]
        )
        page = self.paginate_queryset(related)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(related, many=True)
        return Response(ser.data)
