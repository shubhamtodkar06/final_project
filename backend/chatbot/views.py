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
        import traceback
        user = request.user
        data = request.data
        message = data.get("message", "").strip()
        session_id = data.get("session_id")
        logger.info(f"📥 Incoming chatbot POST | user_id={getattr(user, 'id', None)} | username={getattr(user, 'username', None)} | data={data}")
        print(f"[DEBUG] ChatbotAPIView.post called for user={user.id} with data={data}")
        if not message:
            logger.warning("❗ Empty message received in chatbot POST")
            return Response({"error": "Empty message."}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create chat session
        chat_session = None
        if session_id:
            try:
                chat_session = ChatSession.objects.get(id=session_id)
                logger.info(f"🔎 Found chat session: {session_id}")
            except Exception as e:
                logger.warning(f"⚠️ Could not find chat session {session_id}: {e}")
                print(f"[DEBUG] Could not find chat session {session_id}: {e}")
                chat_session = None
        if not chat_session:
            chat_session = ChatSession.objects.create(user=user)
            session_id = str(chat_session.id)
            logger.info(f"🆕 New chat session created: {session_id} for user {user.id}")
            print(f"[DEBUG] New chat session created: {session_id} for user {user.id}")

        # Store user message
        try:
            ChatMessage.objects.create(session=chat_session, sender="user", content=message)
            logger.info(f"💬 User message stored in session {session_id}")
            print(f"[DEBUG] User message stored in session {session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to store user message: {e}")
            print(f"[DEBUG] Failed to store user message: {e}")

        # Generate response using centralized AI manager (RAG + progress)
        from core.ai_manager import ai_generate
        student_id = str(user.id)
        try:
            answer = ai_generate(student_id, message, mode="chat")
            logger.info(f"🤖 AI response generated (truncated): {str(answer)[:300]}")
            print(f"[DEBUG] AI response (truncated): {str(answer)[:100]}")
        except Exception as e:
            logger.error(f"❌ AI generation failed: {e}\n{traceback.format_exc()}")
            print(f"[DEBUG] AI generation failed: {e}")
            answer = "I'm sorry, I couldn’t process your question right now. Please try again."

        if not answer or "Error:" in answer:
            logger.warning("⚠️ AI returned error or empty response.")
            answer = "I'm sorry, I couldn’t process your question right now. Please try again."

        try:
            ChatMessage.objects.create(session=chat_session, sender="assistant", content=answer)
            logger.info(f"💬 Assistant message stored in session {session_id}")
            print(f"[DEBUG] Assistant message stored in session {session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to store assistant message: {e}")
            print(f"[DEBUG] Failed to store assistant message: {e}")

        # Store in ChatHistory for progress tracking
        try:
            ChatHistory.objects.create(user=user, question=message, answer=answer)
            logger.info(f"🗂️ ChatHistory created for user {user.id}")
            print(f"[DEBUG] ChatHistory created for user {user.id}")
        except Exception as e:
            logger.error(f"❌ Failed to store ChatHistory: {e}")
            print(f"[DEBUG] Failed to store ChatHistory: {e}")

        # No "chunks" variable was defined in the original code; remove from response for now
        return Response({
            "reply": answer,
            "session_id": session_id,
            # "chunks": chunks,
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
        qs = ChatSession.objects.filter(user=self.request.user).order_by("-created_at")
        logger.info(f"🔎 Listing chat sessions for user {self.request.user.id} (found: {qs.count()})")
        print(f"[DEBUG] get_queryset ChatSessionListCreateView: {qs.count()} sessions")
        if not qs:
            logger.warning(f"⚠️ No chat sessions found for user {self.request.user.id}")
        return qs

    def perform_create(self, serializer):
        obj = serializer.save(user=self.request.user)
        logger.info(f"🆕 Chat session created via perform_create: {obj.id}")
        print(f"[DEBUG] perform_create: Chat session {obj.id} created")
    
    def create(self, request, *args, **kwargs):
        title = request.data.get("title") or "New Study Session"
        logger.info(f"📝 Creating chat session for user {request.user.id} with title: {title}")
        print(f"[DEBUG] ChatSessionListCreateView.create: title={title}")
        serializer = self.get_serializer(data={"title": title})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        logger.info(f"✅ Chat session created and serialized for user {request.user.id}")
        print(f"[DEBUG] Chat session created and serialized for user {request.user.id}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChatSessionRetrieveDeleteView(RetrieveDestroyAPIView):
    """
    Retrieve or delete a specific chat session by UUID for the authenticated user.
    """
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "session_id"
    
    def get_queryset(self):
        qs = ChatSession.objects.filter(user=self.request.user)
        logger.info(f"🔎 Retrieve/Delete chat session for user {self.request.user.id} (count: {qs.count()})")
        print(f"[DEBUG] get_queryset ChatSessionRetrieveDeleteView: {qs.count()} sessions")
        if not qs:
            logger.warning(f"⚠️ No chat sessions found for user {self.request.user.id} in Retrieve/Delete")
        return qs


class ChatMessageListView(ListAPIView):
    """
    List all messages in a chat session for the authenticated user.
    """
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session_id = self.kwargs.get("session_id")
        qs = ChatMessage.objects.filter(
            session__id=session_id,
            session__user=self.request.user
        ).order_by("created_at")
        logger.info(f"🔎 Listing messages for session {session_id} (user={self.request.user.id}), found: {qs.count()}")
        print(f"[DEBUG] get_queryset ChatMessageListView: {qs.count()} messages for session {session_id}")
        if not qs:
            logger.warning(f"⚠️ No messages found for session {session_id} and user {self.request.user.id}")
        return qs