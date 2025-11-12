# backend/chatbot/views.py
import logging
from django.conf import settings
from .models import ChatHistory, ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer
from .utils import generate_stream_with_context
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

logger = logging.getLogger(__name__)


class ChatbotAPIView(APIView):
    """
    API endpoint for chatbot interaction with RAG and progress awareness.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        message = data.get("message", "").strip()
        session_id = data.get("session_id")
        if not message:
            return Response({"error": "Empty message."}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create chat session
        chat_session = None
        if session_id:
            try:
                chat_session = ChatSession.objects.get(id=session_id)
            except Exception:
                chat_session = None
        if not chat_session:
            chat_session = ChatSession.objects.create(user=user)
            session_id = str(chat_session.id)

        # Store user message
        ChatMessage.objects.create(session=chat_session, sender="user", content=message)

        # Generate response using centralized AI manager (RAG + progress)
        from core.ai_manager import ai_generate
        student_id = str(user.id)
        answer = ai_generate(student_id, message, mode="chat")
        chunks = [answer]

        # Store assistant message
        ChatMessage.objects.create(session=chat_session, sender="assistant", content=answer)

        # Store in ChatHistory for progress tracking
        ChatHistory.objects.create(user=user, question=message, answer=answer)

        return Response({
            "reply": answer,
            "session_id": session_id,
            "chunks": chunks,
        })


# --- New session/message management views ---
from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated

class ChatSessionListCreateView(ListCreateAPIView):
    """
    List all chat sessions for the authenticated user, or create a new one.
    """
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatSessionRetrieveDeleteView(RetrieveDestroyAPIView):
    """
    Retrieve or delete a specific chat session by UUID for the authenticated user.
    """
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "session_id"

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)


class ChatMessageListView(ListAPIView):
    """
    List all messages in a chat session for the authenticated user.
    """
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session_id = self.kwargs.get("session_id")
        # Only allow if session belongs to user
        return ChatMessage.objects.filter(
            session__id=session_id,
            session__user=self.request.user
        ).order_by("created_at")