# backend/reports/tests.py

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch

from progress.models import Progress


class WeeklyReportViewTestCase(APITestCase):
    """
    Tests for WeeklyReportView:
    - Progress summary generation
    - AI integration
    - Edge cases (no progress)
    - Authentication handling
    """

    def setUp(self):
        # -----------------------------
        # User & Auth
        # -----------------------------
        self.user = User.objects.create_user(
            username="report_user",
            password="Test@123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.url = reverse("weekly_report")

    @patch("reports.views.ai_generate")
    def test_weekly_report_generated_successfully(self, mock_ai):
        """
        Weekly report should be generated when progress exists.
        """
        Progress.objects.create(
            student=self.user,
            subject="Mathematics",
            average_score=62,
            completion_rate=40,
            weak_topics=["Fractions"],
            strong_topics=["Addition"]
        )

        mock_ai.return_value = "This week the student showed moderate improvement in Mathematics."

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("summary", response.data)
        self.assertEqual(response.data["student"], self.user.username)
        self.assertTrue(len(response.data["summary"]) > 0)

    def test_weekly_report_no_progress(self):
        """
        If no progress exists, API should return a safe message.
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "No progress data available.")

    def test_weekly_report_requires_auth(self):
        """
        Weekly report endpoint must require authentication.
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SendParentReportViewTestCase(APITestCase):
    """
    Tests for SendParentReportView:
    - Email sending logic
    - AI report generation
    - Validation errors
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="parent_report_user",
            password="Test@123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.url = reverse("send_parent_report")

        Progress.objects.create(
            student=self.user,
            subject="Science",
            average_score=70,
            completion_rate=55,
            weak_topics=["Light"],
            strong_topics=["Plants"]
        )

    @patch("reports.views.ai_generate")
    @patch("reports.views.send_mail")
    def test_send_parent_report_success(self, mock_send_mail, mock_ai):
        """
        Parent report should be generated and emailed successfully.
        """
        mock_ai.return_value = "Student shows steady progress in Science."
        mock_send_mail.return_value = 1

        payload = {
            "parent_email": "parent@example.com"
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        mock_send_mail.assert_called_once()

    def test_send_parent_report_missing_email(self):
        """
        parent_email is mandatory.
        """
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_send_parent_report_no_progress(self):
        """
        Should fail if no progress data exists.
        """
        Progress.objects.filter(student=self.user).delete()

        response = self.client.post(
            self.url,
            {"parent_email": "parent@example.com"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_send_parent_report_requires_auth(self):
        """
        Authentication required for sending parent report.
        """
        self.client.logout()
        response = self.client.post(
            self.url,
            {"parent_email": "parent@example.com"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)