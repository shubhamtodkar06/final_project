from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch

from progress.models import Progress
from resources.models import Resource


class AIRecommendationsTestCase(APITestCase):
    """
    Tests for AI-based recommendations endpoint.
    Covers:
    - Weak topic extraction
    - AI suggestion generation
    - Resource ranking & filtering
    - Edge cases (no progress / no weak topics)
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="reco_user",
            password="Test@123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.url = reverse("ai_recommendations")

        # Seed Progress
        Progress.objects.create(
            student=self.user,
            subject="Mathematics",
            weak_topics=["Fractions", "Decimals"],
            strong_topics=[],
            average_score=45,
            completion_rate=20
        )

        # Seed Resources
        Resource.objects.create(
            title="Understanding Fractions",
            content="Basics of fractions and operations",
            subject="Mathematics",
            grade_level=5,
            type="system",
            uploaded_by=self.user
        )

        Resource.objects.create(
            title="Decimals Explained",
            content="Decimal numbers and conversions",
            subject="Mathematics",
            grade_level=5,
            type="ai",
            uploaded_by=self.user
        )

        Resource.objects.create(
            title="Algebra Basics",
            content="Intro to algebra",
            subject="Mathematics",
            grade_level=6,
            type="system",
            uploaded_by=self.user
        )

    @patch("recommendations.views.ai_generate")
    def test_recommendations_generated_for_weak_topics(self, mock_ai):
        mock_ai.return_value = "Focus on understanding fractions using visual aids."

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("weak_topics", response.data)
        self.assertIn("ai_suggestion", response.data)
        self.assertGreaterEqual(len(response.data["resources"]), 1)
        self.assertIn("Fractions", response.data["weak_topics"])

    def test_no_weak_topics_returns_empty_recommendations(self):
        Progress.objects.filter(student=self.user).update(weak_topics=[])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["recommendations"], [])
        self.assertEqual(response.data["resources"], [])

    def test_unauthenticated_access_denied(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AIWeeklyStudyStrategyTestCase(APITestCase):
    """
    Tests for AI Weekly Study Strategy endpoint.
    NOTE: This endpoint is POST-only.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="strategy_user",
            password="Test@123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.url = reverse("weekly_study_plan")

    @patch("recommendations.views.ai_generate")
    def test_weekly_study_strategy_generated(self, mock_ai):
        Progress.objects.create(
            student=self.user,
            subject="Science",
            weak_topics=["Light"],
            strong_topics=["Plants"],
            average_score=55,
            completion_rate=30
        )

        mock_ai.return_value = {
            "subject_wise_plan": {"Science": ["Light"]},
            "daily_plan": {
                "Monday": "Revise Light",
                "Sunday": "Rest"
            },
            "revision_strategy": ["Short notes", "Practice questions"]
        }

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("study_strategy", response.data)
        self.assertIn("weak_topics", response.data)
        self.assertIn("strong_topics", response.data)

    def test_weekly_strategy_without_progress_fails(self):
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_weekly_strategy_requires_auth(self):
        self.client.logout()
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)