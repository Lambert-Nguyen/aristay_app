from django.urls import path
from .views import CleaningTaskListCreate, CleaningTaskDetail, UserRegistrationView

urlpatterns = [
    path('cleaning-tasks/', CleaningTaskListCreate.as_view(), name='cleaning-task-list'),
    path('cleaning-tasks/<int:pk>/', CleaningTaskDetail.as_view(), name='cleaning-task-detail'),
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
]