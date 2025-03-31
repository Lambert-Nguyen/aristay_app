from django.urls import path
from .views import CleaningTaskListCreate

urlpatterns = [
    path('cleaning-tasks/', CleaningTaskListCreate.as_view(), name='cleaning-task-list'),
]