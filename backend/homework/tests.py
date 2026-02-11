# backend/homework/tests.py

from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from homework.models import Homework
from progress.models import Progress, StudentTopicProgress
from student_notes.models import Standard, Subject, Topic


# ========= TEST PHASE SWITCHES =========
RUN_BASIC_FLOW = False
RUN_GEMINI_EVALUATION = True
RUN_PROGRESS_UPDATE = False


class HomeworkStepByStepTests(APITestCase):
    """
    Homework tests divided into phases to avoid Gemini quota issues.
    Enable ONE phase at a time.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="hw_student",
            password="Test@1234"
        )
        self.client.force_authenticate(user=self.user)

        self.url = "/api/homework/submit/"

        # Academic setup
        self.standard, _ = Standard.objects.get_or_create(grade=5)
        self.subject, _ = Subject.objects.get_or_create(
            name="Mathematics",
            standard=self.standard
        )
        self.topic, _ = Topic.objects.get_or_create(
            name="Fractions",
            subject=self.subject,
            defaults={"order_index": 0}
        )

        StudentTopicProgress.objects.get_or_create(
            student=self.user,
            topic=self.topic,
            defaults={"status": "available"}
        )

    # ==================================================
    # PHASE 1️⃣ BASIC HOMEWORK FLOW (NO GEMINI CHECK)
    # ==================================================
    def test_01_basic_homework_submission(self):
        if not RUN_BASIC_FLOW:
            self.skipTest("Phase 1 disabled")

        response = self.client.post(
            self.url,
            {
                "subject": "Mathematics",
                "text_content": "Test homework content"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Homework.objects.exists())

        hw = Homework.objects.first()
        self.assertEqual(hw.subject, "Mathematics")

        print("✅ Phase 1 done: Homework saved successfully")

    # ==================================================
    # PHASE 2️⃣ REAL GEMINI RESPONSE VALIDATION
    # ==================================================
    def test_02_gemini_homework_evaluation(self):
        if not RUN_GEMINI_EVALUATION:
            self.skipTest("Phase 2 disabled")

        response = self.client.post(
            self.url,
            {
                "subject": "Mathematics",
                "text_content": "Solve 1/2 + 1/4 and explain steps."
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        hw = Homework.objects.first()
        self.assertIsNotNone(hw.ai_feedback)
        self.assertGreater(hw.score, 0)

        print("\n🧠 Gemini Feedback:")
        print(hw.ai_feedback)
        print("Score:", hw.score)

        print("✅ Phase 2 done: Gemini reply verified")

    # ==================================================
    # PHASE 3️⃣ PROGRESS & TOPIC UPDATE CHECK
    # ==================================================
    def test_03_progress_update_after_homework(self):
        if not RUN_PROGRESS_UPDATE:
            self.skipTest("Phase 3 disabled")

        response = self.client.post(
            self.url,
            {
                "subject": "Mathematics",
                "text_content": "Explain fractions with examples."
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        progress = Progress.objects.filter(
            student=self.user,
            subject="Mathematics"
        ).first()

        self.assertIsNotNone(progress)
        self.assertGreater(progress.average_score, 0)

        topic_progress = StudentTopicProgress.objects.get(
            student=self.user,
            topic=self.topic
        )

        self.assertGreater(topic_progress.mastery_score, 0)

        print("📊 Progress score:", progress.average_score)
        print("📘 Topic mastery:", topic_progress.mastery_score)

        print("✅ Phase 3 done: Progress updated correctly")