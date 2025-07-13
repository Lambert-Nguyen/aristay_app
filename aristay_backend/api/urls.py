from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView,
    TaskViewSet,
    TaskListCreate, TaskDetail,
    PropertyListCreate,
    UserList,
    TaskImageCreateView,
)

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')


urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('', include(router.urls)),
    # nested image-upload on a task:
    path('tasks/<int:task_pk>/images/', TaskImageCreateView.as_view(), name='taskimage-create'),
    path('properties/', PropertyListCreate.as_view(), name='property-list'),
    path('users/', UserList.as_view(), name='user-list'),
]