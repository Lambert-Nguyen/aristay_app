"""
Django management command to clean up old Excel import files.

Usage:
    python manage.py cleanup_old_imports --days 30  # Remove files older than 30 days
    python manage.py cleanup_old_imports --keep 10  # Keep only last 10 imports
    python manage.py cleanup_old_imports --dry-run  # Show what would be deleted
"""

import os
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from api.models import BookingImportLog
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up old Excel import files to save disk space'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Remove files older than this many days (default: 30)'
        )
        parser.add_argument(
            '--keep',
            type=int,
            help='Keep only this many recent imports (overrides --days)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']
        keep = options['keep']
        force = options['force']

        self.stdout.write(
            self.style.SUCCESS(f'Excel Import File Cleanup Tool')
        )

        # Determine which files to delete
        if keep:
            # Keep only the N most recent imports
            import_logs = BookingImportLog.objects.order_by('-imported_at')
            logs_to_delete = import_logs[keep:]
            criteria = f"keeping only {keep} most recent imports"
        else:
            # Delete files older than N days
            cutoff_date = timezone.now() - timedelta(days=days)
            logs_to_delete = BookingImportLog.objects.filter(
                imported_at__lt=cutoff_date
            )
            criteria = f"files older than {days} days (before {cutoff_date.strftime('%Y-%m-%d')})"

        # Collect file information
        files_to_delete = []
        total_size = 0
        
        for log in logs_to_delete:
            if log.import_file:
                file_path = os.path.join(settings.MEDIA_ROOT, log.import_file.name)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    files_to_delete.append({
                        'log': log,
                        'path': file_path,
                        'size': file_size
                    })
                    total_size += file_size

        # Display summary
        if not files_to_delete:
            self.stdout.write(
                self.style.WARNING(f'No files found matching criteria: {criteria}')
            )
            return

        self.stdout.write(f'Found {len(files_to_delete)} files matching criteria: {criteria}')
        self.stdout.write(f'Total disk space to be freed: {self._format_size(total_size)}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n--- DRY RUN MODE - Files that would be deleted: ---'))
        else:
            self.stdout.write('\n--- Files to be deleted: ---')

        for file_info in files_to_delete:
            log = file_info['log']
            size_str = self._format_size(file_info['size'])
            self.stdout.write(
                f"  {log.imported_at.strftime('%Y-%m-%d %H:%M')} | "
                f"{size_str:>8} | "
                f"{log.import_file.name}"
            )

        if dry_run:
            self.stdout.write(self.style.SUCCESS('\nDry run completed. Use --force to actually delete files.'))
            return

        # Confirmation prompt
        if not force:
            confirm = input(f'\nDelete {len(files_to_delete)} files and free {self._format_size(total_size)}? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write('Operation cancelled.')
                return

        # Delete files
        deleted_count = 0
        freed_space = 0
        errors = []

        for file_info in files_to_delete:
            try:
                log = file_info['log']
                file_path = file_info['path']
                file_size = file_info['size']

                # Delete the physical file
                os.remove(file_path)
                
                # Update the database record (clear the file reference)
                log.import_file = None
                log.save()

                deleted_count += 1
                freed_space += file_size
                
                logger.info(f"Deleted import file: {file_path}")

            except Exception as e:
                file_path = file_info.get('path', 'unknown file')
                error_msg = f"Failed to delete {file_path}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        # Summary
        self.stdout.write(f'\n--- Cleanup Summary ---')
        self.stdout.write(f'Files deleted: {deleted_count}')
        self.stdout.write(f'Disk space freed: {self._format_size(freed_space)}')
        
        if errors:
            self.stdout.write(self.style.ERROR(f'Errors: {len(errors)}'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  {error}'))
        else:
            self.stdout.write(self.style.SUCCESS('Cleanup completed successfully!'))

    def _format_size(self, size_bytes):
        """Format file size in human-readable format"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f} TB"
