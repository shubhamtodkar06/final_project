# backend/quiz/tests.py

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch

from quiz.models import Quiz
from progress.models import Progress
from student_notes.models import Standard, Subject, Topic


# ======================================================
# QUIZ GENERATION TESTS
# ======================================================

# backend/quiz/tests.py

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch

from quiz.models import Quiz
from progress.models import Progress, StudentTopicProgress
from student_notes.models import Standard, Subject, Topic


# ======================================================
# QUIZ GENERATION TESTS
# ======================================================

class QuizAPITestCase(APITestCase):
    """
    REST API tests for proactive, filter-based quiz generation.
    """

    def setUp(self):
        # -----------------------------
        # User & Auth
        # -----------------------------
        self.user = User.objects.create_user(
            username="quiz_tester",
            password="Test@123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # -----------------------------
        # Academic Structure (SAFE)
        # -----------------------------
        self.standard, _ = Standard.objects.get_or_create(grade=5)

        self.subject, _ = Subject.objects.get_or_create(
            name="Mathematics",
            standard=self.standard
        )

        self.topic1, _ = Topic.objects.get_or_create(
            name="Fractions",
            subject=self.subject,
            defaults={"order_index": 0}
        )

        self.topic2, _ = Topic.objects.get_or_create(
            name="Decimals",
            subject=self.subject,
            defaults={"order_index": 1}
        )

        # -----------------------------
        # ⭐ Seed Topic Progress (CRITICAL)
        # -----------------------------
        StudentTopicProgress.objects.get_or_create(
            student=self.user,
            topic=self.topic1,
            defaults={
                "status": "in_progress",
                "mastery_score": 30
            }
        )

        # -----------------------------
        # Progress Seed
        # -----------------------------
        Progress.objects.get_or_create(
            student=self.user,
            subject="Mathematics",
            defaults={
                "weak_topics": ["Fractions"],
                "strong_topics": [],
                "average_score": 40,
                "completion_rate": 10
            }
        )

        self.generate_url = reverse("generate_quiz")

    # --------------------------------------------------
    # FILTER-BASED QUIZ
    # --------------------------------------------------
    @patch("quiz.quiz_engine.ai_generate")
    def test_quiz_generation_with_filters(self, mock_ai):
        """
        Quiz generation using subject + topic filters.
        """
        mock_ai.return_value = """
        {
          "questions": [
            {
              "q": "What is 1/2 + 1/2?",
              "options": ["1", "2", "1/4"],
              "correct": "1"
            }
          ]
        }
        """

        payload = {
            "filters": {
                "subjects": ["Mathematics"],
                "topics": ["Fractions"]
            },
            "include_suggestions": False
        }

        response = self.client.post(
            self.generate_url,
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["questions"]), 1)
        self.assertEqual(response.data["final_topics"], ["Fractions"])

        quiz = Quiz.objects.first()
        self.assertEqual(quiz.subject, "Mathematics")
        self.assertEqual(quiz.strategy_used, "proactive")

    # --------------------------------------------------
    # AUTO-SUGGESTION QUIZ
    # --------------------------------------------------
    @patch("quiz.quiz_engine.ai_generate")
    def test_quiz_generation_with_auto_suggestions(self, mock_ai):
        """
        Quiz generation where weak topics are auto-included.
        """
        mock_ai.return_value = """
        {
          "questions": [
            {
              "q": "Convert 0.5 into fraction",
              "options": ["1/2", "1/5"],
              "correct": "1/2"
            }
          ]
        }
        """

        payload = {
            "filters": {
                "subjects": ["Mathematics"]
            },
            "include_suggestions": True
        }

        response = self.client.post(
            self.generate_url,
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Fractions", response.data["final_topics"])
        self.assertTrue(response.data["suggestion_used"])

    # --------------------------------------------------
    # AUTH VALIDATION
    # --------------------------------------------------
    def test_quiz_generation_unauthenticated(self):
        """
        Quiz generation must fail without authentication.
        """
        self.client.logout()

        response = self.client.post(
            self.generate_url,
            {},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        


# ======================================================
# QUIZ SUBMISSION TESTS
# ======================================================

class QuizSubmissionTestCase(APITestCase):
    """
    Tests quiz submission, scoring, and progress updates.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="quiz_submitter",
            password="Test@123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.quiz = Quiz.objects.create(
            student=self.user,
            subject="Science",
            topics=["Light"],
            questions=[
                {
                    "q": "Speed of light?",
                    "options": ["3x10^8 m/s", "300 m/s"],
                    "correct": "3x10^8 m/s"
                }
            ]
        )

        self.submit_url = reverse(
            "submit_quiz",
            kwargs={"quiz_id": self.quiz.id}
        )

    @patch("quiz.views.ai_generate")
    def test_quiz_submission_correct_answer(self, mock_ai):
        """
        Correct quiz submission updates score and progress.
        """
        mock_ai.return_value = "Good performance."

        payload = {"answers": ["3x10^8 m/s"]}

        response = self.client.post(self.submit_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.quiz.refresh_from_db()
        self.assertGreater(self.quiz.score, 0)
        self.assertIsNotNone(self.quiz.ai_feedback)

        progress = Progress.objects.get(student=self.user, subject="Science")
        self.assertIn("Light", progress.strong_topics)

    @patch("quiz.views.ai_generate")
    def test_quiz_submission_wrong_answer(self, mock_ai):
        """
        Wrong answers mark topic as weak.
        """
        mock_ai.return_value = "Needs improvement."

        payload = {"answers": ["300 m/s"]}

        response = self.client.post(self.submit_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        progress = Progress.objects.get(student=self.user, subject="Science")
        self.assertIn("Light", progress.weak_topics)

    def test_quiz_submission_invalid_quiz(self):
        """
        Submitting to a non-existing quiz returns 404.
        """
        url = reverse("submit_quiz", kwargs={"quiz_id": 999})
        response = self.client.post(url, {"answers": []}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ======================================================
# SECURITY TESTS
# ======================================================

class QuizSecurityTests(APITestCase):
    """
    Security and ownership validation.
    """

    def setUp(self):
        self.owner = User.objects.create_user("owner", "owner@test.com", "Test@123")
        self.intruder = User.objects.create_user("intruder", "intr@test.com", "Test@123")

        self.quiz = Quiz.objects.create(
            student=self.owner,
            subject="Math",
            topics=["Numbers"],
            questions=[]
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.intruder)

    def test_cannot_submit_other_users_quiz(self):
        url = reverse("submit_quiz", kwargs={"quiz_id": self.quiz.id})
        response = self.client.post(url, {"answers": []}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)