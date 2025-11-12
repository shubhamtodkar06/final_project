# backend/reports/urls.py
from django.urls import path
from .views import WeeklyReportView

urlpatterns = [
    path("weekly/", WeeklyReportView.as_view(), name="weekly_report"),
]