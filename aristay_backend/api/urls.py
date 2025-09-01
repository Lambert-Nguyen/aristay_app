from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AdminUserCreateView,
    CurrentUserView,
    DeviceRegisterView,
    NotificationListView,
    UserRegistrationView,
    TaskViewSet,
    BookingViewSet,
    PropertyOwnershipViewSet,
    TaskListCreate, TaskDetail,
    PropertyListCreate,
    PropertyDetail,
    UserList,
    TaskImageCreateView,
    TaskImageDetailView,
    AdminInviteUserView,
    AdminPasswordResetView,
    mark_all_notifications_read,
    mark_notification_read,
    unread_notification_count,
    AdminUserDetailView,
    manager_overview,
    ManagerUserList,
    ManagerUserDetail,
    admin_charts_dashboard, system_metrics_dashboard, system_metrics_api,
    system_logs_viewer, system_crash_recovery,
    portal_home, portal_property_list, portal_property_detail, portal_booking_detail,
    portal_task_detail,
    excel_import_view, excel_import_api, property_approval_create,
    enhanced_excel_import_view, enhanced_excel_import_api,
    ConflictReviewView, resolve_conflicts, get_conflict_details,
    preview_conflict_resolution, quick_resolve_conflict,
    file_cleanup_api, user_permissions, available_permissions, 
    manageable_users, grant_permission, revoke_permission, remove_permission_override,
    permission_management_view
)

# Remove separate imports since they're now in the main views.py

from .staff_views import (
    staff_dashboard, cleaning_dashboard, maintenance_dashboard, laundry_dashboard,
    lawn_pool_dashboard, task_detail, update_checklist_response, my_tasks,
    inventory_lookup, log_inventory_transaction, lost_found_list,
    upload_checklist_photo, set_task_status, task_counts_api
)

from .monitoring import (
    HealthCheckView,
    DetailedHealthCheckView,
    log_client_error,
)
from .views import portal_home, portal_property_list, portal_property_detail, portal_booking_detail

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'ownerships', PropertyOwnershipViewSet, basename='ownership')

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('', include(router.urls)),
    path(
        'tasks/<int:task_pk>/images/',
        TaskImageCreateView.as_view(),
        name='taskimage-create'
    ),
    path(
        'tasks/<int:task_pk>/images/<int:pk>/',
        TaskImageDetailView.as_view(),    # ← new detail route
        name='taskimage-detail'
    ),
    path('properties/', PropertyListCreate.as_view(), name='property-list'),
    path('properties/<int:pk>/', PropertyDetail.as_view(), name='property-detail'),
    path('users/', UserList.as_view(), name='user-list'),
    path('admin/invite/', AdminInviteUserView.as_view(), name='admin-invite'),
    path('admin/reset-password/',
         AdminPasswordResetView.as_view(),
         name='admin-reset-password'),
    path('users/me/', CurrentUserView.as_view(), name='current-user'),
    path('admin/create-user/', AdminUserCreateView.as_view(), name='admin-create-user'),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('manager/overview/', manager_overview, name='manager-overview'),
    path('manager/dashboard/', manager_overview, name='manager-dashboard'),  # Alias for compatibility
    path('manager/users/',    ManagerUserList.as_view(),  name='manager-user-list'),
    path('manager/users/<int:pk>/', ManagerUserDetail.as_view(), name='manager-user-detail'),
    path('admin/charts/', admin_charts_dashboard, name='admin-charts'),
    path('admin/dashboard/', admin_charts_dashboard, name='admin-dashboard'),  # Alias for compatibility,
    path('admin/metrics/', system_metrics_dashboard, name='admin-metrics'),
    path('admin/metrics/api/', system_metrics_api, name='admin-metrics-api'),
    path('admin/logs/', system_logs_viewer, name='admin-logs'),
    path('admin/recovery/', system_crash_recovery, name='admin-recovery'),
    path('devices/', DeviceRegisterView.as_view(), name='device-register'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/unread-count/', unread_notification_count, name='notification-unread-count'),
    path('notifications/<int:pk>/read/', mark_notification_read, name='notification-mark-read'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='notification-mark-all-read'),
    
    # Monitoring and health check endpoints
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('health/detailed/', DetailedHealthCheckView.as_view(), name='detailed-health-check'),
    path('log-client-error/', log_client_error, name='log-client-error'),

    # Portal (web) routes
    path('portal/', portal_home, name='portal-home'),
    path('portal/properties/', portal_property_list, name='portal-properties'),
    path('portal/properties/<int:pk>/', portal_property_detail, name='portal-property-detail'),
    path('portal/properties/<int:property_id>/bookings/<int:pk>/', portal_booking_detail, name='portal-booking-detail'),
    path('portal/tasks/<int:task_id>/', portal_task_detail, name='portal-task-detail'),
    
    # Staff Portal Routes
    path('staff/', staff_dashboard, name='staff-dashboard'),
    path('staff/cleaning/', cleaning_dashboard, name='cleaning-dashboard'),
    path('staff/maintenance/', maintenance_dashboard, name='maintenance-dashboard'),
    path('staff/laundry/', laundry_dashboard, name='laundry-dashboard'),
    path('staff/lawn_pool/', lawn_pool_dashboard, name='lawn-pool-dashboard'),
    path('staff/tasks/', my_tasks, name='staff-tasks'),
    path('staff/tasks/<int:task_id>/', task_detail, name='staff-task-detail'),
    path('staff/inventory/', inventory_lookup, name='staff-inventory'),
    path('staff/lost-found/', lost_found_list, name='staff-lost-found'),
    
    # Staff AJAX endpoints
    path('staff/checklist-response/<int:response_id>/update/', update_checklist_response, name='update-checklist-response'),
    path('staff/inventory/transaction/', log_inventory_transaction, name='log-inventory-transaction'),
    path('staff/checklist-photo/upload/', upload_checklist_photo, name='upload-checklist-photo'),
    path('staff/task-counts/', task_counts_api, name='staff-task-counts'),
    path('tasks/<int:task_id>/set_status/', set_task_status, name='set-task-status'),
    
    # Excel Import endpoints
    path('excel-import/', excel_import_view, name='excel-import'),
    path('excel-import/api/', excel_import_api, name='excel-import-api'),
    path('excel-import-with-conflicts/', excel_import_view, name='excel_import_with_conflicts'),
    path('property-approval/create/', property_approval_create, name='property-approval-create'),
    
    # Enhanced Excel Import endpoints
    path('enhanced-excel-import/', enhanced_excel_import_view, name='enhanced-excel-import'),
    path('enhanced-excel-import/api/', enhanced_excel_import_api, name='enhanced-excel-import-api'),
    path('manager/enhanced-excel-import/', enhanced_excel_import_view, name='manager-enhanced-excel-import'),
    path('admin/enhanced-excel-import/', enhanced_excel_import_view, name='admin-enhanced-excel-import'),
    
    # Conflict Resolution endpoints
    path('admin/conflict-review/<int:import_session_id>/', ConflictReviewView.as_view(), name='conflict-review'),
    path('resolve-conflicts/<int:import_session_id>/', resolve_conflicts, name='resolve-conflicts'),
    path('conflict-details/<int:import_session_id>/', get_conflict_details, name='conflict-details'),
    path('preview-conflict/<int:import_session_id>/<int:conflict_index>/', preview_conflict_resolution, name='preview-conflict-resolution'),
    path('quick-resolve/<int:import_session_id>/<int:conflict_index>/', quick_resolve_conflict, name='quick-resolve-conflict'),
    
    # File Cleanup endpoints
    path('file-cleanup/api/', file_cleanup_api, name='file-cleanup-api'),
    
    # Permission Management API endpoints
    path('permissions/user/', user_permissions, name='user-permissions'),
    path('permissions/available/', available_permissions, name='available-permissions'),
    path('permissions/manageable-users/', manageable_users, name='manageable-users'),
    path('permissions/grant/', grant_permission, name='grant-permission'),
    path('permissions/revoke/', revoke_permission, name='revoke-permission'),
    path('permissions/remove-override/', remove_permission_override, name='remove-permission-override'),
    
    # Permission Management UI
    path('admin/permissions/', permission_management_view, name='permission-management'),
]