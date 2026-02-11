# backend/resources/tests.py

from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch

from resources.models import Resource


class ResourceIngestionAPITestCase(APITestCase):
    """
    Comprehensive tests for Resource ingestion module.

    Covers:
    - Authentication
    - Text-based resource ingestion
    - File-based ingestion (PDF / Image)
    - Edge cases & validation
    - AI / embedding side-effects (mocked)
    """

    def setUp(self):
        # -----------------------------
        # User & Auth
        # -----------------------------
        self.user = User.objects.create_user(
            username="resource_user",
            password="Test@123"
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.url = reverse("add_resource")

    # -------------------------------------------------
    # BASIC TEXT INGESTION
    # -------------------------------------------------
    @patch("resources.utils.generate_embeddings")
    def test_add_resource_text_only(self, mock_embeddings):
        """
        Should successfully ingest a text-based resource.
        """
        mock_embeddings.return_value = [0.1] * 768

        payload = {
            "title": "Algebra Basics",
            "content": "This resource explains basic algebra concepts.",
            "subject": "Mathematics",
            "grade_level": 5,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Resource.objects.count(), 1)

        resource = Resource.objects.first()
        self.assertEqual(resource.title, "Algebra Basics")
        self.assertEqual(resource.subject, "Mathematics")
        self.assertEqual(resource.grade_level, 5)
        self.assertIsNotNone(resource.content)

    # -------------------------------------------------
    # FILE INGESTION (IMAGE)
    # -------------------------------------------------
    @patch("resources.utils.extract_text_from_file")
    @patch("resources.utils.generate_embeddings")
    def test_add_resource_image_file(self, mock_embeddings, mock_ocr):
        """
        Should ingest an image resource and extract text using OCR.
        """
        mock_ocr.return_value = "Extracted text from image"
        mock_embeddings.return_value = [0.2] * 768

        image_file = SimpleUploadedFile(
            "notes.jpg",
            b"fake-image-bytes",
            content_type="image/jpeg"
        )

        payload = {
            "title": "Science Diagram",
            "content": "",
            "subject": "Science",
            "grade_level": 6,
            "file": image_file
        }

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        resource = Resource.objects.first()
        self.assertIn("Extracted text", resource.extracted_text)

    # -------------------------------------------------
    # FILE INGESTION (PDF)
    # -------------------------------------------------
    @patch("resources.utils.extract_text_from_file")
    @patch("resources.utils.generate_embeddings")
    def test_add_resource_pdf_file(self, mock_embeddings, mock_ocr):
        """
        Should ingest a PDF resource and extract text.
        """
        mock_ocr.return_value = "Extracted text from PDF"
        mock_embeddings.return_value = [0.3] * 768

        pdf_file = SimpleUploadedFile(
            "chapter1.pdf",
            b"%PDF-1.4 fake content",
            content_type="application/pdf"
        )

        payload = {
            "title": "History Chapter",
            "content": "",
            "subject": "History",
            "grade_level": 7,
            "file": pdf_file
        }

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        resource = Resource.objects.first()
        self.assertTrue(resource.extracted_text)

    # -------------------------------------------------
    # VALIDATION ERRORS
    # -------------------------------------------------
    def test_missing_required_fields(self):
        """
        Missing title / subject / grade_level should fail.
        """
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------
    # AUTHENTICATION
    # -------------------------------------------------
    def test_add_resource_requires_auth(self):
        """
        Endpoint must reject unauthenticated requests.
        """
        self.client.logout()

        payload = {
            "title": "Unauthorized Resource",
            "content": "Should not be saved",
            "subject": "Math",
            "grade_level": 5
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # -------------------------------------------------
    # EDGE CASE: EMPTY CONTENT AND NO FILE
    # -------------------------------------------------
    def test_add_resource_empty_content_and_no_file(self):
        """
        Should reject request if neither content nor file is provided.
        """
        payload = {
            "title": "Empty Resource",
            "content": "",
            "subject": "Geography",
            "grade_level": 8
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------
    # MULTIPLE RESOURCES
    # -------------------------------------------------
    @patch("resources.utils.generate_embeddings")
    def test_multiple_resource_ingestion(self, mock_embeddings):
        """
        Should allow ingestion of multiple resources sequentially.
        """
        mock_embeddings.return_value = [0.5] * 768

        for i in range(3):
            payload = {
                "title": f"Resource {i}",
                "content": f"Content {i}",
                "subject": "Math",
                "grade_level": 5
            }
            response = self.client.post(self.url, payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Resource.objects.count(), 3)