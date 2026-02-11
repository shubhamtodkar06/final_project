# backend/reports/urls.py
from django.urls import path
from .views import WeeklyReportView
from .views import SendParentReportView

urlpatterns = [
    path("weekly/", WeeklyReportView.as_view(), name="weekly_report"),
]

urlpatterns += [
    path("send-to-parent/", SendParentReportView.as_view(), name="send_parent_report"),
]