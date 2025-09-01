"""
Simple Django management command for file cleanup.

Usage:
    python manage.py cleanup_imports --days 30       # Remove files older than 30 days
    python manage.py cleanup_imports --stats         # Show storage statistics
    python manage.py cleanup_imports --suggest 100   # Suggest cleanup to stay under 100MB
    python manage.py cleanup_imports --dry-run       # Show what would be deleted
"""

from django.core.management.base import BaseCommand
from api.services.file_cleanup_service import ImportFileCleanupService


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
            '--stats',
            action='store_true',
            help='Show current storage statistics'
        )
        parser.add_argument(
            '--suggest',
            type=int,
            help='Suggest cleanup strategy to stay under N MB'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        if options['stats']:
            self._show_stats()
        elif options['suggest']:
            self._show_suggestions(options['suggest'])
        else:
            self._perform_cleanup(options['days'], options['dry_run'])

    def _show_stats(self):
        """Show current storage statistics"""
        self.stdout.write(self.style.SUCCESS('📊 Excel Import File Storage Statistics'))
        self.stdout.write('=' * 50)
        
        stats = ImportFileCleanupService.get_storage_stats()
        
        self.stdout.write(f"Total Files: {stats['total_files']}")
        self.stdout.write(f"Total Size: {stats['total_size_mb']:.1f} MB ({stats['total_size_gb']:.2f} GB)")
        
        if stats['oldest_file'] and stats['newest_file']:
            self.stdout.write(f"Date Range: {stats['oldest_file']} to {stats['newest_file']}")
            self.stdout.write(f"Age Span: {stats['age_span_days']} days")
        
        if stats['total_size_mb'] > 100:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️  Storage is {stats['total_size_mb']:.1f} MB. Consider cleanup!")
            )

    def _show_suggestions(self, target_mb):
        """Show cleanup suggestions"""
        self.stdout.write(self.style.SUCCESS(f'💡 Cleanup Suggestions (Target: {target_mb} MB)'))
        self.stdout.write('=' * 50)
        
        suggestion = ImportFileCleanupService.suggest_cleanup(target_mb)
        
        self.stdout.write(f"Current Size: {suggestion['current_size_mb']:.1f} MB")
        self.stdout.write(f"Target Size: {suggestion['target_size_mb']} MB")
        
        if not suggestion['action_needed']:
            self.stdout.write(self.style.SUCCESS("✅ " + suggestion['message']))
        else:
            if 'recommended_days_to_keep' in suggestion:
                self.stdout.write(self.style.WARNING("📋 Recommendation:"))
                self.stdout.write(f"  • Keep files from last {suggestion['recommended_days_to_keep']} days")
                self.stdout.write(f"  • Delete {suggestion['files_to_delete']} files")
                self.stdout.write(f"  • Free {suggestion['space_to_free_mb']:.1f} MB")
                self.stdout.write(f"  • Final size: {suggestion['projected_final_size_mb']:.1f} MB")
                self.stdout.write(f"\nTo execute: python manage.py cleanup_imports --days {suggestion['recommended_days_to_keep']}")
            else:
                self.stdout.write(self.style.ERROR("❌ " + suggestion['message']))
                self.stdout.write(self.style.WARNING("💡 " + suggestion['recommendation']))

    def _perform_cleanup(self, days, dry_run):
        """Perform the actual cleanup"""
        action = "🔍 Dry Run" if dry_run else "🗑️  Cleanup"
        self.stdout.write(self.style.SUCCESS(f'{action}: Removing files older than {days} days'))
        self.stdout.write('=' * 50)
        
        result = ImportFileCleanupService.cleanup_old_files(days, dry_run)
        
        self.stdout.write(f"Files found: {result['files_found']}")
        self.stdout.write(f"Total size: {result['total_size_mb']:.1f} MB")
        self.stdout.write(f"Cutoff date: {result['cutoff_date']}")
        
        if dry_run:
            if result['files_found'] > 0:
                self.stdout.write(self.style.WARNING(f"\n📁 Files that would be deleted:"))
                for file_info in result['files'][:5]:  # Show first 5
                    date_str = file_info['imported_at'].strftime('%Y-%m-%d')
                    size_mb = file_info['size'] / (1024 * 1024)
                    self.stdout.write(f"  {date_str} | {size_mb:.1f} MB | {file_info['file_name']}")
                
                if len(result['files']) > 5:
                    self.stdout.write(f"  ... and {len(result['files']) - 5} more files")
                
                self.stdout.write(f"\nTo actually delete: python manage.py cleanup_imports --days {days}")
            else:
                self.stdout.write(self.style.SUCCESS("✅ No files need cleanup"))
        else:
            if result['files_deleted'] > 0:
                self.stdout.write(self.style.SUCCESS(f"\n✅ Cleanup completed!"))
                self.stdout.write(f"Files deleted: {result['files_deleted']}")
                self.stdout.write(f"Space freed: {result['space_freed_mb']:.1f} MB")
                
                if result['errors']:
                    self.stdout.write(self.style.ERROR(f"\n❌ Errors: {len(result['errors'])}"))
                    for error in result['errors']:
                        self.stdout.write(self.style.ERROR(f"  {error}"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ No files needed cleanup"))
