"""
Audit Event Pruning Management Command
=====================================
Prune old audit events to keep database lean without losing recent forensics.

Usage:
    python manage.py prune_audit --days 90

Cron suggestion:
    0 3 * * * python manage.py prune_audit --days 90
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.models import AuditEvent

class Command(BaseCommand):
    help = "Delete AuditEvent rows older than --days (default 90)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=90, 
                          help="Delete audit events older than this many days")
        parser.add_argument("--dry-run", action="store_true",
                          help="Show what would be deleted without actually deleting")

    def handle(self, *args, **opts):
        cutoff = timezone.now() - timedelta(days=opts["days"])
        qs = AuditEvent.objects.filter(created_at__lt=cutoff)
        count = qs.count()
        
        if opts["dry_run"]:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would delete {count} audit events older than {opts['days']} days")
            )
            return
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(f"No audit events found older than {opts['days']} days")
            )
            return
        
        # Delete in batches for large datasets
        batch_size = 1000
        deleted_total = 0
        
        while True:
            batch_qs = qs[:batch_size]
            if not batch_qs.exists():
                break
            
            batch_count = batch_qs.count()
            batch_qs.delete()
            deleted_total += batch_count
            
            self.stdout.write(f"Deleted batch of {batch_count} audit events...")
        
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted_total} audit events older than {opts['days']} days")
        )
