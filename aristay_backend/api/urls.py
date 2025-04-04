from django.urls import path
from .views import CleaningTaskListCreate, CleaningTaskDetail

urlpatterns = [
    path('cleaning-tasks/', CleaningTaskListCreate.as_view(), name='cleaning-task-list'),
    path('cleaning-tasks/<int:pk>/', CleaningTaskDetail.as_view(), name='cleaning-task-detail'),
]