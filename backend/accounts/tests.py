# backend/accounts/tests.py

from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from accounts.models import StudentProfile
from student_notes.models import Standard, Subject, Topic
from progress.models import StudentTopicProgress


# ======================================================
# AUTH TESTS
# ======================================================

class AccountsAuthTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/auth/register/"
        self.login_url = "/api/auth/login/"
        self.profile_url = "/api/auth/profile/"

    # -----------------------------
    # REGISTER
    # -----------------------------
    def test_user_registration_success(self):
        # FIX 1: Added first_name and last_name to payload
        response = self.client.post(
            self.register_url,
            {
                "username": "student1",
                "password": "Test@1234",
                "password2": "Test@1234",
                "email": "student1@test.com",
                "first_name": "Student",  # Added
                "last_name": "One",       # Added
            },
            format="json",
        )

        # Accept successful creation
        self.assertIn(
            response.status_code,
            [status.HTTP_201_CREATED, status.HTTP_200_OK]
        )

        self.assertTrue(
            User.objects.filter(username="student1").exists()
        )

    def test_user_registration_password_mismatch(self):
        # FIX 2: Added first_name/last_name here too to isolate password error
        response = self.client.post(
            self.register_url,
            {
                "username": "student2",
                "password": "Test@1234",
                "password2": "WrongPass",
                "email": "student2@test.com",
                "first_name": "Student",
                "last_name": "Two",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_username_registration(self):
        User.objects.create_user(username="student3", password="Test@1234")

        response = self.client.post(
            self.register_url,
            {
                "username": "student3",
                "password": "Test@1234",
                "password2": "Test@1234",
                "email": "dup@test.com",
                "first_name": "Student",
                "last_name": "Three",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -----------------------------
    # LOGIN
    # -----------------------------
    def test_login_success(self):
        User.objects.create_user(username="student4", password="Test@1234")

        response = self.client.post(
            self.login_url,
            {
                "username": "student4",
                "password": "Test@1234",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "unknown",
                "password": "wrong",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # -----------------------------
    # PROFILE ACCESS
    # -----------------------------
    def test_profile_requires_auth(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_access_authenticated(self):
        user = User.objects.create_user(username="student5", password="Test@1234")
        self.client.force_authenticate(user=user)

        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "student5")


# ======================================================
# PROFILE SETUP + LEARNING PATH
# ======================================================

class StudentProfileSetupTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="student6", password="Test@1234")
        self.client.force_authenticate(user=self.user)
        self.setup_url = "/api/auth/profile/setup/"

        # Idempotent academic seed
        self.standard, _ = Standard.objects.get_or_create(grade=5)
        self.subject, _ = Subject.objects.get_or_create(
            name="Mathematics",
            standard=self.standard
        )

        self.topic1, _ = Topic.objects.get_or_create(
            name="Numbers",
            subject=self.subject,
            defaults={"order_index": 0}
        )
        # FIX 3: Explicitly enforce order index to prevent sorting ambiguity
        self.topic1.order_index = 0
        self.topic1.save()

        self.topic2, _ = Topic.objects.get_or_create(
            name="Fractions",
            subject=self.subject,
            defaults={"order_index": 1}
        )
        # FIX 3: Explicitly enforce order index
        self.topic2.order_index = 1
        self.topic2.save()

    def test_profile_setup_success(self):
        response = self.client.post(
            self.setup_url,
            {"grade": 5, "board": "CBSE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            StudentProfile.objects.filter(user=self.user).exists()
        )

    def test_profile_update_existing(self):
        StudentProfile.objects.create(user=self.user, grade=4, board="ICSE")

        response = self.client.post(
            self.setup_url,
            {"grade": 5, "board": "CBSE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile = StudentProfile.objects.get(user=self.user)
        self.assertEqual(profile.grade, 5)
        self.assertEqual(profile.board, "CBSE")

    def test_missing_grade(self):
        response = self.client.post(
            self.setup_url,
            {"board": "CBSE"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -----------------------------
    # AUTO TOPIC UNLOCKING
    # -----------------------------
    def test_first_topic_auto_unlocked(self):
        self.client.post(
            self.setup_url,
            {"grade": 5, "board": "CBSE"},
            format="json",
        )

        progress = StudentTopicProgress.objects.get(
            student=self.user,
            topic=self.topic1
        )

        self.assertEqual(progress.status, "available")

    def test_next_topic_locked_initially(self):
        self.client.post(
            self.setup_url,
            {"grade": 5, "board": "CBSE"},
            format="json",
        )

        progress = StudentTopicProgress.objects.get(
            student=self.user,
            topic=self.topic2
        )

        self.assertEqual(progress.status, "locked")


# ======================================================
# SECURITY / TOKEN EDGE CASES
# ======================================================

class AccountsSecurityEdgeTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.profile_url = "/api/auth/profile/"

    def test_profile_without_token(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_with_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)