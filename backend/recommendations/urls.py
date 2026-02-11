from django.urls import path
from .views import AIRecommendationsView, AIWeeklyStudyStrategyView

urlpatterns = [
    path("ai/", AIRecommendationsView.as_view(), name="ai_recommendations"),
    path("study-plan/", AIWeeklyStudyStrategyView.as_view(), name="weekly_study_plan"),
]