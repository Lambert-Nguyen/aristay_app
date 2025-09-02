#!/usr/bin/env python3
"""
Automated Excel Import File Cleanup Script

This script can be run as a cron job to automatically clean up old Excel import files.

Usage:
    python cleanup_cron.py --days 30        # Remove files older than 30 days
    python cleanup_cron.py --target-mb 100  # Keep only enough files to stay under 100MB

Add to crontab for weekly cleanup:
    0 2 * * 0 cd /path/to/aristay_backend && python cleanup_cron.py --days 30

Add to crontab for daily size-based cleanup:
    0 1 * * * cd /path/to/aristay_backend && python cleanup_cron.py --target-mb 50
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from api.services.file_cleanup_service import ImportFileCleanupService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/file_cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Automated Excel import file cleanup')
    parser.add_argument('--days', type=int, help='Remove files older than N days')
    parser.add_argument('--target-mb', type=int, help='Keep files to stay under N MB')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted')
    parser.add_argument('--quiet', action='store_true', help='Only log errors')
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    try:
        if args.target_mb:
            # Size-based cleanup
            logger.info(f"Starting size-based cleanup (target: {args.target_mb} MB)")
            
            # Get current stats
            stats = ImportFileCleanupService.get_storage_stats()
            logger.info(f"Current storage: {stats['total_files']} files, {stats['total_size_mb']:.1f} MB")
            
            if stats['total_size_mb'] <= args.target_mb:
                logger.info("Storage is already within target limits")
                return
            
            # Get recommendation
            suggestion = ImportFileCleanupService.suggest_cleanup(args.target_mb)
            
            if not suggestion['action_needed']:
                logger.info("No cleanup needed")
                return
            
            if 'recommended_days_to_keep' not in suggestion:
                logger.warning("Cannot reach target size even with aggressive cleanup")
                return
            
            days_to_keep = suggestion['recommended_days_to_keep']
            logger.info(f"Recommended strategy: keep last {days_to_keep} days")
            
            # Perform cleanup
            result = ImportFileCleanupService.cleanup_old_files(days_to_keep, args.dry_run)
            
        elif args.days:
            # Time-based cleanup
            logger.info(f"Starting time-based cleanup (remove files older than {args.days} days)")
            result = ImportFileCleanupService.cleanup_old_files(args.days, args.dry_run)
            
        else:
            # Default: 30 days
            logger.info("Starting default cleanup (remove files older than 30 days)")
            result = ImportFileCleanupService.cleanup_old_files(30, args.dry_run)
        
        # Log results
        if args.dry_run:
            if result['files_found'] > 0:
                logger.info(f"DRY RUN: Would delete {result['files_found']} files ({result['total_size_mb']:.1f} MB)")
            else:
                logger.info("DRY RUN: No files need cleanup")
        else:
            if result['files_deleted'] > 0:
                logger.info(f"SUCCESS: Deleted {result['files_deleted']} files, freed {result['space_freed_mb']:.1f} MB")
                
                if result.get('errors'):
                    logger.warning(f"Encountered {len(result['errors'])} errors during cleanup")
                    for error in result['errors']:
                        logger.error(error)
            else:
                logger.info("No files needed cleanup")
        
        # Log final stats
        final_stats = ImportFileCleanupService.get_storage_stats()
        logger.info(f"Final storage: {final_stats['total_files']} files, {final_stats['total_size_mb']:.1f} MB")
        
    except Exception as e:
        logger.error(f"Cleanup script failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
