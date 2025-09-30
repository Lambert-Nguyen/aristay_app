from django.core.management.base import BaseCommand
from api.models import TaskImage
from django.db.models import Q


class Command(BaseCommand):
    help = 'Clean up TaskImage objects that have no associated files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find TaskImage objects without files
        broken_images = TaskImage.objects.filter(
            Q(image__isnull=True) | Q(image='')
        )
        
        count = broken_images.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No broken photo records found.')
            )
            return
        
        self.stdout.write(f'Found {count} broken photo records:')
        
        for img in broken_images:
            self.stdout.write(
                f'  - ID: {img.id}, Task: {img.task.title}, '
                f'Type: {img.photo_type}, Status: {img.photo_status}'
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} broken photo records. '
                    'Run without --dry-run to actually delete them.'
                )
            )
        else:
            # Delete the broken records
            deleted_count, _ = broken_images.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_count} broken photo records.'
                )
            )


