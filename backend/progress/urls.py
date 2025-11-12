# backend/progress/urls.py
from django.urls import path
from .views import ProgressListView, ProgressUpdateView, ProgressOverviewView

urlpatterns = [
    path("", ProgressListView.as_view(), name="progress-list"),
    path("<int:pk>/", ProgressUpdateView.as_view(), name="progress-update"),
    path("overview/", ProgressOverviewView.as_view(), name="progress-overview"),
]

from .views import ProgressSubjectView, ProgressTrendView

urlpatterns += [
    path("subject/<str:subject>/", ProgressSubjectView.as_view(), name="progress-subject"),
    path("trend/", ProgressTrendView.as_view(), name="progress-trend"),
]

from .views import ProgressAnalyticsView

urlpatterns += [
    path("analytics/", ProgressAnalyticsView.as_view(), name="progress-analytics"),
]

# --- Deep Analytics endpoint ---
from .views import ProgressDeepInsightsView

urlpatterns += [
    path("analytics/deep/", ProgressDeepInsightsView.as_view(), name="progress-analytics-deep"),
]