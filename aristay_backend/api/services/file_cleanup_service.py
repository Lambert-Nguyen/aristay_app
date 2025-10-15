"""
File Cleanup Utilities for Excel Import System

This module provides utilities for cleaning up old Excel import files
to prevent disk space from growing indefinitely.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from api.models import BookingImportLog

logger = logging.getLogger(__name__)


class ImportFileCleanupService:
    """Service for cleaning up old Excel import files"""
    
    @staticmethod
    def cleanup_old_files(days_to_keep: int = 30, dry_run: bool = False) -> Dict[str, Any]:
        """
        Clean up Excel import files older than specified days.
        
        Args:
            days_to_keep: Keep files newer than this many days (default: 30)
            dry_run: If True, only show what would be deleted without deleting
        
        Returns:
            Dictionary with cleanup results
        """
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Find old import logs with files
        old_logs = BookingImportLog.objects.filter(
            imported_at__lt=cutoff_date,
            import_file__isnull=False
        ).exclude(import_file='')
        
        files_info = []
        total_size = 0
        
        for log in old_logs:
            if log.import_file:
                try:
                    file_path = os.path.join(settings.MEDIA_ROOT, log.import_file.name)
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        files_info.append({
                            'log_id': log.pk,
                            'file_path': file_path,
                            'file_name': log.import_file.name,
                            'size': file_size,
                            'imported_at': log.imported_at
                        })
                        total_size += file_size
                except Exception as e:
                    logger.warning(f"Could not get info for file {log.import_file.name}: {e}")
        
        result = {
            'files_found': len(files_info),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
            'days_to_keep': days_to_keep,
            'dry_run': dry_run
        }
        
        if dry_run:
            result['files'] = files_info
            return result
        
        # Actually delete files
        deleted_count = 0
        freed_space = 0
        errors = []
        
        for file_info in files_info:
            try:
                os.remove(file_info['file_path'])
                
                # Update the database record (clear the file reference)
                log = BookingImportLog.objects.get(pk=file_info['log_id'])
                log.import_file.delete(save=False)  # Delete file reference
                log.save()
                
                deleted_count += 1
                freed_space += file_info['size']
                
                logger.info(f"Deleted old import file: {file_info['file_name']}")
                
            except Exception as e:
                error_msg = f"Failed to delete {file_info['file_name']}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        result.update({
            'files_deleted': deleted_count,
            'space_freed_bytes': freed_space,
            'space_freed_mb': round(freed_space / (1024 * 1024), 2),
            'errors': errors
        })
        
        if deleted_count > 0:
            logger.info(f"Cleanup completed: {deleted_count} files deleted, {result['space_freed_mb']} MB freed")
        
        return result
    
    @staticmethod
    def get_storage_stats() -> Dict[str, Any]:
        """Get current storage statistics for import files"""
        import_logs = BookingImportLog.objects.filter(
            import_file__isnull=False
        ).exclude(import_file='')
        
        total_files = 0
        total_size = 0
        oldest_file = None
        newest_file = None
        
        for log in import_logs:
            if log.import_file:
                try:
                    file_path = os.path.join(settings.MEDIA_ROOT, log.import_file.name)
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        total_files += 1
                        total_size += file_size
                        
                        if oldest_file is None or log.imported_at < oldest_file:
                            oldest_file = log.imported_at
                        if newest_file is None or log.imported_at > newest_file:
                            newest_file = log.imported_at
                            
                except Exception as e:
                    logger.warning(f"Could not get info for file {log.import_file.name}: {e}")
        
        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
            'oldest_file': oldest_file.strftime('%Y-%m-%d') if oldest_file else None,
            'newest_file': newest_file.strftime('%Y-%m-%d') if newest_file else None,
            'age_span_days': (newest_file - oldest_file).days if oldest_file and newest_file else 0
        }
    
    @staticmethod
    def suggest_cleanup(target_size_mb: int = 100) -> Dict[str, Any]:
        """
        Suggest how many days of files to keep to stay under target size.
        
        Args:
            target_size_mb: Target total size in MB
        
        Returns:
            Cleanup recommendation
        """
        current_stats = ImportFileCleanupService.get_storage_stats()
        
        if current_stats['total_size_mb'] <= target_size_mb:
            return {
                'current_size_mb': current_stats['total_size_mb'],
                'target_size_mb': target_size_mb,
                'action_needed': False,
                'message': 'Current storage is within target limits'
            }
        
        # Try different retention periods to find one that fits
        for days in [7, 14, 30, 60, 90]:
            cleanup_result = ImportFileCleanupService.cleanup_old_files(
                days_to_keep=days, 
                dry_run=True
            )
            
            projected_size = current_stats['total_size_mb'] - cleanup_result['total_size_mb']
            
            if projected_size <= target_size_mb:
                return {
                    'current_size_mb': current_stats['total_size_mb'],
                    'target_size_mb': target_size_mb,
                    'action_needed': True,
                    'recommended_days_to_keep': days,
                    'files_to_delete': cleanup_result['files_found'],
                    'space_to_free_mb': cleanup_result['total_size_mb'],
                    'projected_final_size_mb': projected_size,
                    'message': f'Keep last {days} days of files to reach target size'
                }
        
        return {
            'current_size_mb': current_stats['total_size_mb'],
            'target_size_mb': target_size_mb,
            'action_needed': True,
            'message': 'Even keeping only 7 days of files would exceed target size',
            'recommendation': 'Consider using cloud storage or increasing target size'
        }
