# api/filters.py
from django_filters import rest_framework as filters
from django.utils import timezone

from .models import Task

class TaskFilter(filters.FilterSet):
    # adds ?overdue=true to mean “due_date < now AND not completed/canceled”
    overdue = filters.BooleanFilter(method='filter_overdue')

    class Meta:
        model = Task
        fields = {
            # from your old filterset_fields
            'property_ref': ['exact'],
            'status':       ['exact'],
            'assigned_to':  ['exact'],
            # add filters for created_at, modified_at, due_date
            'created_at':   ['exact', 'gte', 'lte'],
            'modified_at':  ['exact', 'gte', 'lte'],
            'due_date':     ['exact', 'gte', 'lte'],
            # also allow filtering by task_type
            'task_type':    ['exact'],
            # you could even filter by who created/modified
            'created_by':   ['exact'],
            'modified_by':  ['exact'],
        }

    def filter_overdue(self, queryset, name, value):
        if value:
            now = timezone.now()
            return (
                queryset
                  .filter(due_date__isnull=False, due_date__lt=now)
                  .exclude(status__in=['completed', 'canceled'])
            )
        return queryset