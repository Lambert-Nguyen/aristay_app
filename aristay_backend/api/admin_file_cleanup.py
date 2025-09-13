"""
Django Admin Actions for File Cleanup

This adds admin actions to manage Excel import file cleanup directly from
the Django admin interface.
"""

from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import path
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from api.services.file_cleanup_service import ImportFileCleanupService


class FileCleanupAdminMixin:
    """Mixin to add file cleanup actions to admin classes"""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'file-cleanup/',
                self.admin_site.admin_view(self.file_cleanup_view),
                name='api_file_cleanup'
            ),
        ]
        return custom_urls + urls
    
    def file_cleanup_view(self, request):
        """File cleanup management view"""
        if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role in ['manager', 'superuser'])):
            raise PermissionDenied
        
        context = {
            'title': 'Excel Import File Cleanup',
            'opts': self.model._meta,
            'has_view_permission': True,
        }
        
        if request.method == 'POST':
            action = request.POST.get('action')
            days = int(request.POST.get('days', 30))
            
            if action == 'stats':
                stats = ImportFileCleanupService.get_storage_stats()
                context['stats'] = stats
                
            elif action == 'suggest':
                target_mb = int(request.POST.get('target_mb', 100))
                suggestion = ImportFileCleanupService.suggest_cleanup(target_mb)
                context['suggestion'] = suggestion
                
            elif action == 'dry_run':
                result = ImportFileCleanupService.cleanup_old_files(days, dry_run=True)
                context['dry_run_result'] = result
                
            elif action == 'cleanup':
                result = ImportFileCleanupService.cleanup_old_files(days, dry_run=False)
                if result['files_deleted'] > 0:
                    messages.success(
                        request, 
                        f"Successfully deleted {result['files_deleted']} files and freed {result['space_freed_mb']:.1f} MB"
                    )
                else:
                    messages.info(request, "No files needed cleanup")
                context['cleanup_result'] = result
        
        # Always show current stats
        if 'stats' not in context:
            context['stats'] = ImportFileCleanupService.get_storage_stats()
        
        return render(request, 'admin/file_cleanup.html', context)


# Custom admin actions
def cleanup_files_7_days(modeladmin, request, queryset):
    """Admin action to cleanup files older than 7 days"""
    result = ImportFileCleanupService.cleanup_old_files(7, dry_run=False)
    if result['files_deleted'] > 0:
        messages.success(
            request, 
            f"Cleanup completed: {result['files_deleted']} files deleted, {result['space_freed_mb']:.1f} MB freed"
        )
    else:
        messages.info(request, "No files needed cleanup (older than 7 days)")

cleanup_files_7_days.short_description = "🗑️ Cleanup files older than 7 days"


def cleanup_files_30_days(modeladmin, request, queryset):
    """Admin action to cleanup files older than 30 days"""
    result = ImportFileCleanupService.cleanup_old_files(30, dry_run=False)
    if result['files_deleted'] > 0:
        messages.success(
            request, 
            f"Cleanup completed: {result['files_deleted']} files deleted, {result['space_freed_mb']:.1f} MB freed"
        )
    else:
        messages.info(request, "No files needed cleanup (older than 30 days)")

cleanup_files_30_days.short_description = "🗑️ Cleanup files older than 30 days"


def show_storage_stats(modeladmin, request, queryset):
    """Admin action to show storage statistics"""
    stats = ImportFileCleanupService.get_storage_stats()
    messages.info(
        request,
        f"Storage Stats: {stats['total_files']} files, {stats['total_size_mb']:.1f} MB total, "
        f"age span: {stats['age_span_days']} days"
    )

show_storage_stats.short_description = "📊 Show storage statistics"
