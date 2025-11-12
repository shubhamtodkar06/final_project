# backend/chatbot/consumers.py
import logging
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from rest_framework_simplejwt.tokens import AccessToken, TokenError

from .models import ChatSession, ChatMessage, ChatHistory
from core.ai_manager import ai_generate
from .tts import synthesize_text

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer that supports:
    - Optional JWT auth via ?token=<access_token>
    - Session-aware chat (create/use ChatSession)
    - RAG-backed AI via core.ai_manager.ai_generate
    - Optional TTS -> base64 WAV
    - Structured messages: status, partial, final, error
    """

    async def connect(self):
        self.user = await self._get_user_from_token()
        await self.accept()
        uname = getattr(self.user, "username", "AnonymousUser")
        logger.info(f"✅ WebSocket connected: {uname}")
        await self.send_json({"message": "Connected to AI Chatbot!"})

    async def receive_json(self, content, **kwargs):
        """
        Expected payload:
        {
          "message": "Explain supervised learning.",
          "session_id": "uuid-string",   # optional
          "subject": "Mathematics",      # optional
          "tts": true                    # optional
        }
        """
        try:
            text = (content.get("message") or "").strip()
            if not text:
                await self.send_json({"error": "Empty message."})
                return

            session_id = content.get("session_id")
            subject = content.get("subject")
            tts_flag = bool(content.get("tts", False))

            session = await self._get_or_create_session(session_id)

            # store user message if authenticated
            if not isinstance(self.user, AnonymousUser):
                await sync_to_async(ChatMessage.objects.create)(
                    session=session, sender="user", content=text
                )

            await self.send_json(
                {"type": "status", "value": "typing", "session_id": str(session.id)}
            )

            student_id = getattr(self.user, "id", None)
            reply = await sync_to_async(ai_generate)(
                student_id, text, mode="chat", subject=subject
            )

            # optional "partial" teaser (simulated)
            if isinstance(reply, str) and len(reply) > 160:
                await self.send_json(
                    {
                        "type": "partial",
                        "text": reply[:160] + "...",
                        "session_id": str(session.id),
                    }
                )

            audio_b64 = None
            content_type = None
            if tts_flag:
                try:
                    audio_b64 = await sync_to_async(synthesize_text)(reply)
                    content_type = "audio/wav"
                except Exception as e:
                    logger.error(f"🎤 TTS generation failed: {e}")
                    await self.send_json({"type": "warning", "tts_error": str(e)})

            # store assistant & flat history if authenticated
            if not isinstance(self.user, AnonymousUser):
                await sync_to_async(ChatMessage.objects.create)(
                    session=session, sender="assistant", content=reply
                )
                await sync_to_async(ChatHistory.objects.create)(
                    user=self.user, question=text, answer=reply, created_at=timezone.now()
                )

            payload = {"type": "final", "reply": reply, "session_id": str(session.id)}
            if audio_b64:
                payload.update({"audio_b64": audio_b64, "content_type": content_type})
            await self.send_json(payload)

        except Exception as e:
            logger.exception("❌ WebSocket internal error")
            await self.send_json({"error": f"Internal error: {e}"})

    async def disconnect(self, close_code):
        uname = getattr(self.user, "username", "AnonymousUser")
        logger.info(f"🔌 WebSocket disconnected ({close_code}): {uname}")

    async def _get_user_from_token(self):
        """Authenticate via ?token=<access> in querystring; else AnonymousUser."""
        try:
            query = parse_qs(self.scope.get("query_string", b"").decode())
            token = (query.get("token") or [None])[0]
            if not token:
                return AnonymousUser()
            token = token.strip().lstrip("<").rstrip(">")
            access = AccessToken(token)
            user_id = access.get("user_id")
            if not user_id:
                return AnonymousUser()
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = await sync_to_async(User.objects.get)(id=user_id)
            return user
        except (TokenError, Exception) as e:
            logger.warning(f"JWT auth failed: {e}")
            return AnonymousUser()

    async def _get_or_create_session(self, session_id):
        """Return ChatSession; create new if missing/invalid."""
        try:
            if session_id:
                session = await sync_to_async(ChatSession.objects.get)(id=session_id)
                return session
        except ChatSession.DoesNotExist:
            pass

        kwargs = {"title": "New Chat Session"}
        if not isinstance(self.user, AnonymousUser):
            kwargs["user"] = self.user
        session = await sync_to_async(ChatSession.objects.create)(**kwargs)
        return session