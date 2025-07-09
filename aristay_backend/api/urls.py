from django.urls import path
from .views import (
    UserRegistrationView,
    TaskListCreate, TaskDetail,
    PropertyListCreate,
    UserList,   # ← import it
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('tasks/',     TaskListCreate.as_view(),    name='task-list'),
    path('tasks/<int:pk>/', TaskDetail.as_view(),   name='task-detail'),
    path('properties/', PropertyListCreate.as_view(), name='property-list'),
    path('users/',     UserList.as_view(),          name='user-list'),
]