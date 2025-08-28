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
    admin_charts_dashboard,    
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
    path('manager/users/',    ManagerUserList.as_view(),  name='manager-user-list'),
    path('manager/users/<int:pk>/', ManagerUserDetail.as_view(), name='manager-user-detail'),
    path('admin/charts/', admin_charts_dashboard, name='admin-charts'),
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
]