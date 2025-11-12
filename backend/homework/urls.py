# backend/homework/urls.py
from django.urls import path
from .views import SubmitHomeworkView

urlpatterns = [
    path('submit/', SubmitHomeworkView.as_view(), name='submit-homework'),
]