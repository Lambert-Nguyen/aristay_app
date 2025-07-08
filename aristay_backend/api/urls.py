from django.urls import path
from .views import TaskListCreate, TaskDetail, UserRegistrationView, PropertyListCreate

urlpatterns = [
    path('tasks/', TaskListCreate.as_view(), name='task-list'),
    path('tasks/<int:pk>/', TaskDetail.as_view(), name='task-detail'),
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('properties/', PropertyListCreate.as_view(), name='property-list'),
]