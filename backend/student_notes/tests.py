from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import StudentProfile
from student_notes.models import Standard, Subject, Topic, MasterNote, AINote
from progress.models import StudentTopicProgress


class StudentNotesTestCase(TestCase):
    """
    Complete test suite for Student Notes module.
    """

    def setUp(self):
        # -----------------------------
        # User & Auth
        # -----------------------------
        self.user = User.objects.create_user(
            username="student1",
            password="Test@123"
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # -----------------------------
        # Academic Structure
        # -----------------------------
        self.standard, _ = Standard.objects.get_or_create(grade=5)

        self.subject_math, _ = Subject.objects.get_or_create(
            name="Mathematics",
            standard=self.standard
        )

        self.subject_science, _ = Subject.objects.get_or_create(
            name="Science",
            standard=self.standard
        )

        self.topic_frac, _ = Topic.objects.get_or_create(
            name="Fractions",
            subject=self.subject_math,
            order_index=1
        )

        self.topic_dec, _ = Topic.objects.get_or_create(
            name="Decimals",
            subject=self.subject_math,
            order_index=2
        )

        self.topic_cells, _ = Topic.objects.get_or_create(
            name="Cells",
            subject=self.subject_science,
            order_index=1
        )

        # -----------------------------
        # Student Profile
        # -----------------------------
        StudentProfile.objects.get_or_create(
            user=self.user,
            grade=5,
            board="CBSE"
        )

        # -----------------------------
        # Master Notes
        # -----------------------------
        MasterNote.objects.get_or_create(
            standard=self.standard,
            subject=self.subject_math,
            topic=self.topic_frac,
            content="Fractions are parts of a whole.",
            source="admin"
        )

        MasterNote.objects.get_or_create(
            standard=self.standard,
            subject=self.subject_math,
            topic=self.topic_dec,
            content="Decimals represent fractional values.",
            source="teacher"
        )

        # -----------------------------
        # Topic Progress (for suggestions)
        # -----------------------------
        StudentTopicProgress.objects.get_or_create(
            student=self.user,
            topic=self.topic_frac,
            status="in_progress",
            mastery_score=40
        )

        StudentTopicProgress.objects.get_or_create(
            student=self.user,
            topic=self.topic_dec,
            status="available",
            mastery_score=0
        )

        # URLs
        self.generate_url = reverse("notes-generate")
        self.global_url = reverse("notes-global")
        self.subject_url = reverse("notes-subject", args=["Mathematics"])
        self.topic_url = reverse("notes-topic", args=["Mathematics", "Fractions"])

    # --------------------------------------------------
    # GENERATE NOTES (FILTER BASED)
    # --------------------------------------------------
    def test_generate_notes_with_manual_filters(self):
        payload = {
            "filters": {
                "subjects": ["Mathematics"],
                "topics": ["Fractions"]
            },
            "include_suggestions": False
        }

        response = self.client.post(self.generate_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("notes", response.data)
        self.assertGreaterEqual(len(response.data["notes"]), 1)

        self.assertEqual(AINote.objects.count(), 1)

    # --------------------------------------------------
    # GENERATE NOTES (PROACTIVE)
    # --------------------------------------------------
    def test_generate_notes_with_proactive_suggestions(self):
        payload = {
            "filters": {
                "subjects": ["Mathematics"]
            },
            "include_suggestions": True
        }

        response = self.client.post(self.generate_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("suggestions", response.data)
        self.assertGreaterEqual(len(response.data["final_topics"]), 1)

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------
    def test_generate_notes_without_subject(self):
        payload = {
            "filters": {
                "topics": ["Fractions"]
            }
        }

        response = self.client.post(self.generate_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --------------------------------------------------
    # READ APIs
    # --------------------------------------------------
    def test_get_global_notes(self):
        response = self.client.get(self.global_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_get_subject_notes(self):
        response = self.client.get(self.subject_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(
            note["subject"] == "Mathematics"
            for note in response.data
        ))

    def test_get_topic_notes(self):
        response = self.client.get(self.topic_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(
            note["topic"] == "Fractions"
            for note in response.data
        ))

    # --------------------------------------------------
    # AUTH
    # --------------------------------------------------
    def test_notes_requires_auth(self):
        self.client.logout()
        response = self.client.get(self.global_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --------------------------------------------------
    # GRADE ISOLATION
    # --------------------------------------------------
    def test_notes_not_shared_across_grades(self):
        std6, _ = Standard.objects.get_or_create(grade=6)
        subj6, _ = Subject.objects.get_or_create(name="Mathematics", standard=std6)
        topic6, _ = Topic.objects.get_or_create(name="Fractions", subject=subj6)

        MasterNote.objects.get_or_create(
            standard=std6,
            subject=subj6,
            topic=topic6,
            content="Grade 6 fractions",
            source="admin"
        )

        response = self.client.get(self.subject_url)
        contents = [note["content"] for note in response.data]

        self.assertNotIn("Grade 6 fractions", contents)