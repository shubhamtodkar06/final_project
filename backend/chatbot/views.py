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
from progress.suggestion_engine import suggest_topics

logger = logging.getLogger(__name__)


class ChatbotAPIView(APIView):
    """
    API endpoint for chatbot interaction with:
    ✔ RAG
    ✔ Progress awareness
    ✔ Proactive topic suggestions
    ✔ Filter merging (user + AI suggested)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        import traceback

        user = request.user
        data = request.data
        message = data.get("message", "").strip()
        session_id = data.get("session_id")

        logger.info(
            f"📥 Incoming chatbot POST | user_id={getattr(user, 'id', None)} "
            f"| username={getattr(user, 'username', None)} | data={data}"
        )

        if not message:
            return Response({"error": "Empty message."}, status=status.HTTP_400_BAD_REQUEST)

        # ---------------------------------------------------
        # SESSION MANAGEMENT (UNCHANGED)
        # ---------------------------------------------------
        chat_session = None

        if session_id:
            try:
                chat_session = ChatSession.objects.get(id=session_id)
            except Exception:
                chat_session = None

        if not chat_session:
            chat_session = ChatSession.objects.create(user=user)
            session_id = str(chat_session.id)

        # ---------------------------------------------------
        # STORE USER MESSAGE
        # ---------------------------------------------------
        try:
            ChatMessage.objects.create(
                session=chat_session,
                sender="user",
                content=message
            )
        except Exception as e:
            logger.error(f"❌ Failed storing user message: {e}")

        # ---------------------------------------------------
        # ⭐ PROACTIVE FILTER ENGINE
        # ---------------------------------------------------
        from core.ai_manager import ai_generate

        student_id = str(user.id)

        incoming_filters = data.get("filters", {}) or {}
        include_suggestions = data.get("include_suggestions", True)

        subjects = incoming_filters.get("subjects", [])
        user_topics = set(incoming_filters.get("topics", []))

        suggestions = {}

        # ----- Suggest Topics Based on Progress -----
        if include_suggestions and subjects:
            try:
                suggestions = suggest_topics(user, subjects)

                for topic_group in suggestions.values():
                    user_topics.update(topic_group)

            except Exception as e:
                logger.warning(f"⚠️ Topic suggestion failed: {e}")

        final_filters = {
            "subjects": subjects,
            "topics": list(user_topics)
        }

        # ---------------------------------------------------
        # AI GENERATION (RAG + PROGRESS + FILTERS)
        # ---------------------------------------------------
        try:
            answer = ai_generate(
                student_id=student_id,
                query=message,
                mode="chat",
                filters=final_filters,
                scope="filtered"
            )

        except Exception as e:
            logger.error(f"❌ AI generation failed: {e}\n{traceback.format_exc()}")
            answer = "I'm sorry, I couldn’t process your question right now. Please try again."

        if not answer or "Error:" in answer:
            answer = "I'm sorry, I couldn’t process your question right now. Please try again."

        # ---------------------------------------------------
        # STORE ASSISTANT MESSAGE
        # ---------------------------------------------------
        try:
            ChatMessage.objects.create(
                session=chat_session,
                sender="assistant",
                content=answer
            )
        except Exception as e:
            logger.error(f"❌ Failed storing assistant message: {e}")

        # ---------------------------------------------------
        # STORE CHAT HISTORY (ANALYTICS)
        # ---------------------------------------------------
        try:
            ChatHistory.objects.create(
                user=user,
                question=message,
                answer=answer
            )
        except Exception as e:
            logger.error(f"❌ Failed storing ChatHistory: {e}")

        # ---------------------------------------------------
        # RESPONSE WITH PROACTIVE METADATA
        # ---------------------------------------------------
        return Response({
            "reply": answer,
            "session_id": session_id,
            "filters_used": final_filters,
            "suggested_topics": suggestions,
            "suggestion_enabled": include_suggestions
        })


# ============================================================
# SESSION MANAGEMENT VIEWS (UNCHANGED)
# ============================================================

from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView, ListAPIView


class ChatSessionListCreateView(ListCreateAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(
            user=self.request.user
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        title = request.data.get("title") or "New Study Session"

        serializer = self.get_serializer(data={"title": title})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChatSessionRetrieveDeleteView(RetrieveDestroyAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "session_id"

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)


class ChatMessageListView(ListAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session_id = self.kwargs.get("session_id")

        return ChatMessage.objects.filter(
            session__id=session_id,
            session__user=self.request.user
        ).order_by("created_at")