#backend/recommendations/urls.py
from django.urls import path
from .views import AIRecommendationsView

urlpatterns = [
    path("ai/", AIRecommendationsView.as_view(), name="ai_recommendations"),
    path("personal/", AIRecommendationsView.as_view(), name="personal_recommendations"),  # placeholder for personalized endpoint
]