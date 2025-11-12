# backend/progress/urls.py
from django.urls import path
from .views import ProgressListView, ProgressUpdateView, ProgressOverviewView

urlpatterns = [
    path("", ProgressListView.as_view(), name="progress-list"),
    path("<int:pk>/", ProgressUpdateView.as_view(), name="progress-update"),
    path("overview/", ProgressOverviewView.as_view(), name="progress-overview"),
]