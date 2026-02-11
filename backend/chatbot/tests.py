# backend/chatbot/tests.py

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from channels.testing import WebsocketCommunicator
from myproject.asgi import application

from chatbot.models import ChatSession, ChatMessage
import json


# ==========================================================
# REST API TESTS – CHATBOT
# ==========================================================

class ChatbotRESTTestCase(APITestCase):
    """
    Tests REST-based chatbot functionality:
    - Authenticated chat
    - Filters
    - Session handling
    - Edge cases
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="student5",
            password="Test@1234"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.chat_url = "/api/chatbot/chat/"

    def test_basic_chat_message(self):
        """Simple chat message without filters"""
        response = self.client.post(
            self.chat_url,
            {"message": "Explain fractions"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("reply", response.data)
        self.assertIn("session_id", response.data)

    def test_chat_with_filters(self):
        """Chat with subject filter"""
        response = self.client.post(
            self.chat_url,
            {
                "message": "Explain fractions",
                "filters": {
                    "subjects": ["Mathematics"]
                }
            },
            format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("reply", response.data)

    def test_chat_with_session_reuse(self):
        """Reuse an existing chat session"""
        first = self.client.post(
            self.chat_url,
            {"message": "What is a fraction?"},
            format="json"
        )
        session_id = first.data["session_id"]

        second = self.client.post(
            self.chat_url,
            {
                "message": "Give an example",
                "session_id": session_id
            },
            format="json"
        )

        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["session_id"], session_id)

    def test_empty_message(self):
        """Empty message should fail"""
        response = self.client.post(
            self.chat_url,
            {"message": ""},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chat_message_persistence(self):
        """Ensure messages are saved in DB"""
        self.client.post(
            self.chat_url,
            {"message": "Explain fractions"},
            format="json"
        )
        self.assertEqual(ChatMessage.objects.count(), 2)  # user + assistant


# ==========================================================
# WEBSOCKET TESTS – CHATBOT
# ==========================================================

from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import AccessToken
from channels.testing import WebsocketCommunicator
from myproject.asgi import application


class ChatbotWebSocketTestCase(TransactionTestCase):
    """
    Tests WebSocket chatbot:
    - JWT auth
    - Message send/receive
    - Streaming format
    - TTS flow
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="student_ws",
            password="Test@1234"
        )

        token = AccessToken.for_user(self.user)
        self.ws_url = f"/ws/chat/?token={str(token)}"

    async def test_websocket_connection_success(self):
        communicator = WebsocketCommunicator(application, self.ws_url)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_websocket_send_receive(self):
        communicator = WebsocketCommunicator(application, self.ws_url)
        await communicator.connect()

        # Skip welcome message
        await communicator.receive_json_from()

        await communicator.send_json_to({
            "message": "Explain fractions",
            "filters": {
                "subjects": ["Mathematics"]
            }
        })

        # Expect status + final
        received_final = False

        for _ in range(5):
            response = await communicator.receive_json_from(timeout=3)
            if response.get("type") == "final":
                received_final = True
                self.assertIn("reply", response)
                break

        self.assertTrue(received_final)
        await communicator.disconnect()

    async def test_websocket_tts_flow(self):
        communicator = WebsocketCommunicator(application, self.ws_url)
        await communicator.connect()

        # Skip welcome
        await communicator.receive_json_from()

        await communicator.send_json_to({
            "message": "Explain fractions",
            "tts": True
        })

        received_types = set()

        for _ in range(6):
            msg = await communicator.receive_json_from(timeout=3)
            if msg.get("type"):
                received_types.add(msg["type"])

        self.assertIn("final", received_types)
        # TTS is optional depending on credentials
        await communicator.disconnect()

    async def test_websocket_auth_failure(self):
        communicator = WebsocketCommunicator(
            application,
            "/ws/chat/?token=invalidtoken"
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

# ==========================================================
# EDGE CASES & REGRESSION TESTS
# ==========================================================

class ChatbotEdgeCaseTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="edgecase",
            password="Test@1234"
        )
        self.client.force_authenticate(user=self.user)

    def test_large_input(self):
        """Very large input should not crash"""
        large_text = "Explain fractions. " * 500
        response = self.client.post(
            "/api/chatbot/chat/",
            {"message": large_text},
            format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_filters(self):
        """Invalid filters should fallback safely"""
        response = self.client.post(
            "/api/chatbot/chat/",
            {
                "message": "Explain fractions",
                "filters": {
                    "subjects": ["NonExistingSubject"]
                }
            },
            format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("reply", response.data)