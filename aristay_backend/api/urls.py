from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminUserCreateView,
    CurrentUserView,
    DeviceRegisterView,
    NotificationListView,
    UserRegistrationView,
    TaskViewSet,
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
)

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')

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
    path('devices/', DeviceRegisterView.as_view(), name='device-register'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/unread-count/', unread_notification_count, name='notification-unread-count'),
    path('notifications/<int:pk>/read/', mark_notification_read, name='notification-mark-read'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='notification-mark-all-read'),
]