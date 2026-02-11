# backend/progress/tests.py

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from progress.models import Progress, StudentTopicProgress
from progress.utils import (
    update_progress_on_quiz,
    update_progress_on_homework
)
from progress.suggestion_engine import suggest_topics
from progress.topic_engine import update_topic_mastery, unlock_next_topic

from student_notes.models import Standard, Subject, Topic


class ProgressModelTests(APITestCase):
    """
    Tests basic Progress and StudentTopicProgress model behavior.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="progress_user",
            password="Test@123"
        )

        self.standard = Standard.objects.create(grade=5)
        self.subject = Subject.objects.create(
            name="Mathematics",
            standard=self.standard
        )

        self.topic1 = Topic.objects.create(
            name="Fractions",
            subject=self.subject,
            order_index=0
        )
        self.topic2 = Topic.objects.create(
            name="Decimals",
            subject=self.subject,
            order_index=1
        )

    def test_progress_creation(self):
        progress = Progress.objects.create(
            student=self.user,
            subject="Mathematics"
        )
        self.assertEqual(progress.average_score, 0)
        self.assertEqual(progress.completion_rate, 0)

    def test_student_topic_progress_creation(self):
        stp = StudentTopicProgress.objects.create(
            student=self.user,
            topic=self.topic1,
            status="available"
        )
        self.assertEqual(stp.mastery_score, 0)
        self.assertEqual(stp.status, "available")


class ProgressUtilsQuizTests(APITestCase):
    """
    Tests quiz-based progress updates.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="quiz_user",
            password="Test@123"
        )

        self.standard = Standard.objects.create(grade=6)
        self.subject = Subject.objects.create(
            name="Science",
            standard=self.standard
        )

        self.topic1 = Topic.objects.create(
            name="Light",
            subject=self.subject,
            order_index=0
        )
        self.topic2 = Topic.objects.create(
            name="Sound",
            subject=self.subject,
            order_index=1
        )

    def test_update_progress_on_quiz_basic(self):
        update_progress_on_quiz(
            student=self.user,
            subject="Science",
            correct_topics=["Light"],
            wrong_topics=["Sound"]
        )

        progress = Progress.objects.get(
            student=self.user,
            subject="Science"
        )

        self.assertIn("Light", progress.strong_topics)
        self.assertIn("Sound", progress.weak_topics)
        self.assertGreater(progress.average_score, 0)
        self.assertGreater(progress.completion_rate, 0)

    def test_quiz_progress_creates_progress_if_missing(self):
        self.assertFalse(
            Progress.objects.filter(
                student=self.user,
                subject="Science"
            ).exists()
        )

        update_progress_on_quiz(
            student=self.user,
            subject="Science",
            correct_topics=[],
            wrong_topics=["Light"]
        )

        self.assertTrue(
            Progress.objects.filter(
                student=self.user,
                subject="Science"
            ).exists()
        )


class ProgressUtilsHomeworkTests(APITestCase):
    """
    Tests homework-based progress updates.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="hw_user",
            password="Test@123"
        )

    def test_update_progress_on_homework_first_attempt(self):
        update_progress_on_homework(
            student=self.user,
            subject="English",
            score=70
        )

        progress = Progress.objects.get(
            student=self.user,
            subject="English"
        )

        self.assertEqual(progress.average_score, 70)
        self.assertGreater(progress.completion_rate, 0)

    def test_update_progress_on_homework_rolling_average(self):
        update_progress_on_homework(
            student=self.user,
            subject="English",
            score=60
        )
        update_progress_on_homework(
            student=self.user,
            subject="English",
            score=80
        )

        progress = Progress.objects.get(
            student=self.user,
            subject="English"
        )

        self.assertGreaterEqual(progress.average_score, 60)
        self.assertLessEqual(progress.average_score, 80)


class TopicMasteryEngineTests(APITestCase):
    """
    Tests topic mastery and automatic unlocking.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="mastery_user",
            password="Test@123"
        )

        self.standard = Standard.objects.create(grade=7)
        self.subject = Subject.objects.create(
            name="History",
            standard=self.standard
        )

        self.topic1 = Topic.objects.create(
            name="Ancient India",
            subject=self.subject,
            order_index=0
        )
        self.topic2 = Topic.objects.create(
            name="Medieval India",
            subject=self.subject,
            order_index=1
        )

        StudentTopicProgress.objects.create(
            student=self.user,
            topic=self.topic1,
            status="available"
        )

    def test_topic_mastery_increases_score(self):
        update_topic_mastery(self.user, self.topic1, 80)

        stp = StudentTopicProgress.objects.get(
            student=self.user,
            topic=self.topic1
        )

        self.assertGreater(stp.mastery_score, 0)
        self.assertIn(stp.status, ["in_progress", "mastered"])

    def test_unlock_next_topic_on_mastery(self):
        update_topic_mastery(self.user, self.topic1, 95)

        self.assertTrue(
            StudentTopicProgress.objects.filter(
                student=self.user,
                topic=self.topic2
            ).exists()
        )


class SuggestionEngineTests(APITestCase):
    """
    Tests proactive topic suggestion logic.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="suggest_user",
            password="Test@123"
        )

        self.standard = Standard.objects.create(grade=8)
        self.subject = Subject.objects.create(
            name="Geography",
            standard=self.standard
        )

        self.topic1 = Topic.objects.create(
            name="Climate",
            subject=self.subject,
            order_index=0
        )
        self.topic2 = Topic.objects.create(
            name="Rivers",
            subject=self.subject,
            order_index=1
        )

        StudentTopicProgress.objects.create(
            student=self.user,
            topic=self.topic1,
            status="in_progress",
            mastery_score=40
        )

        StudentTopicProgress.objects.create(
            student=self.user,
            topic=self.topic2,
            status="available",
            mastery_score=0
        )

    def test_suggest_topics_returns_structure(self):
        suggestions = suggest_topics(self.user, subjects=["Geography"])

        self.assertIn("weak", suggestions)
        self.assertIn("in_progress", suggestions)
        self.assertIn("next_topics", suggestions)

    def test_weak_topic_detection(self):
        suggestions = suggest_topics(self.user)

        self.assertIn("Climate", suggestions["weak"])


class ProgressAPIEndpointTests(APITestCase):
    """
    Tests REST endpoints for progress analytics.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="api_user",
            password="Test@123"
        )
        self.client.force_authenticate(user=self.user)

        Progress.objects.create(
            student=self.user,
            subject="Math",
            average_score=75,
            completion_rate=40,
            weak_topics=["Algebra"],
            strong_topics=["Numbers"]
        )

    def test_progress_list_endpoint(self):
        response = self.client.get("/api/progress/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_progress_overview_endpoint(self):
        response = self.client.get("/api/progress/overview/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("average_score", response.data)

    def test_subject_progress_endpoint(self):
        response = self.client.get("/api/progress/subject/Math/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)