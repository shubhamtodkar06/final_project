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
from progress.suggestion_engine import suggest_topics   # ⭐ NEW

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer that supports:

    ✔ JWT auth
    ✔ Session chat
    ✔ RAG
    ✔ Proactive filter merging
    ✔ Topic suggestions
    ✔ TTS
    ✔ Streaming
    """

    async def connect(self):
        self.user = await self._get_user_from_token()

        # ⭐ STRICT AUTH CHECK
        if isinstance(self.user, AnonymousUser):
            logger.warning("❌ WebSocket rejected: Invalid or expired token")
            await self.close(code=4001)  # Auth failed
            return

        await self.accept()

        uname = getattr(self.user, "username", "AnonymousUser")
        logger.info(f"✅ WebSocket connected: {uname}")

        await self.send_json({"message": "Connected to AI Chatbot!"})


    async def receive_json(self, content, **kwargs):
        """
        Expected Payload:
        {
          "message": "Explain supervised learning",
          "session_id": "uuid",        # optional
          "filters": {                 # ⭐ NEW
              "subjects": ["Math"],
              "topics": ["Fractions"]
          },
          "include_suggestions": true, # ⭐ NEW
          "tts": true
        }
        """

        import time
        from datetime import datetime

        try:
            text = (content.get("message") or "").strip()
            if not text:
                await self.send_json({"error": "Empty message."})
                return

            session_id = content.get("session_id")
            filters = content.get("filters", {}) or {}
            include_suggestions = content.get("include_suggestions", True)
            tts_flag = bool(content.get("tts", False))

            session = await self._get_or_create_session(session_id)

            # ---------------------------------------------------
            # Store user message
            # ---------------------------------------------------
            if not isinstance(self.user, AnonymousUser):
                await sync_to_async(ChatMessage.objects.create)(
                    session=session,
                    sender="user",
                    content=text
                )

            # ---------------------------------------------------
            # ⭐ PROACTIVE FILTER ENGINE
            # ---------------------------------------------------
            subjects = filters.get("subjects", [])
            user_topics = set(filters.get("topics", []))
            suggestions = {}

            if include_suggestions and subjects:
                try:
                    suggestions = await sync_to_async(suggest_topics)(
                        self.user,
                        subjects
                    )

                    for topic_group in suggestions.values():
                        user_topics.update(topic_group)

                except Exception as e:
                    logger.warning(f"Suggestion failed: {e}")

            final_filters = {
                "subjects": subjects,
                "topics": list(user_topics)
            }

            # ---------------------------------------------------
            # Status typing
            # ---------------------------------------------------
            await self.send_json({
                "type": "status",
                "value": "typing",
                "session_id": str(session.id),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })

            # ---------------------------------------------------
            # AI Generation
            # ---------------------------------------------------
            student_id = getattr(self.user, "id", None)

            start_ts = time.time()
            reply = None
            error_reply = None

            try:
                reply = await sync_to_async(ai_generate)(
                    student_id,
                    text,
                    mode="chat",
                    filters=final_filters,
                    scope="filtered"
                )

                ai_latency = time.time() - start_ts

            except Exception as e:
                ai_latency = time.time() - start_ts
                logger.error(f"AI generation failed: {e}")
                reply = f"AI error: {e}"
                error_reply = reply

            # ---------------------------------------------------
            # Streaming Simulation
            # ---------------------------------------------------
            now_iso = datetime.utcnow().isoformat() + "Z"

            if isinstance(reply, str) and len(reply) > 160:
                await self.send_json({
                    "type": "partial",
                    "text": reply[:160] + "...",
                    "session_id": str(session.id),
                    "timestamp": now_iso,
                })

            final_payload = {
                "type": "final",
                "reply": reply,
                "session_id": str(session.id),
                "timestamp": now_iso,
                "latency_ms": int(ai_latency * 1000),
                "filters_used": final_filters,              # ⭐ NEW
                "suggested_topics": suggestions,            # ⭐ NEW
                "suggestion_enabled": include_suggestions   # ⭐ NEW
            }

            await self.send_json(final_payload)

            # ---------------------------------------------------
            # ⭐ TTS Support
            # ---------------------------------------------------
            if tts_flag and reply and not error_reply:
                try:
                    tts_start = time.time()

                    audio_b64 = await sync_to_async(synthesize_text)(reply)

                    await self.send_json({
                        "type": "tts",
                        "audio_b64": audio_b64,
                        "content_type": "audio/wav",
                        "session_id": str(session.id),
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "tts_latency_ms": int((time.time() - tts_start) * 1000),
                    })

                except Exception as e:
                    logger.error(f"TTS failed: {e}")

            # ---------------------------------------------------
            # Save assistant + history
            # ---------------------------------------------------
            if not isinstance(self.user, AnonymousUser):

                await sync_to_async(ChatMessage.objects.create)(
                    session=session,
                    sender="assistant",
                    content=reply
                )

                await sync_to_async(ChatHistory.objects.create)(
                    user=self.user,
                    question=text,
                    answer=reply,
                    created_at=timezone.now()
                )

        except Exception as e:
            logger.exception("❌ WS internal error")

            await self.send_json({
                "error": f"Internal error: {e}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })


    async def disconnect(self, close_code):
        uname = getattr(self.user, "username", "AnonymousUser")
        logger.info(f"🔌 WebSocket disconnected ({close_code}): {uname}")


    async def _get_user_from_token(self):
        try:
            query = parse_qs(self.scope.get("query_string", b"").decode())
            token = (query.get("token") or [None])[0]

            if not token:
                return AnonymousUser()

            token = token.strip().lstrip("<").rstrip(">")
            access = AccessToken(token)

            user_id = access.get("user_id")

            from django.contrib.auth import get_user_model
            User = get_user_model()

            return await sync_to_async(User.objects.get)(id=user_id)

        except (TokenError, Exception) as e:
            logger.warning(f"JWT auth failed: {e}")
            return AnonymousUser()


    async def _get_or_create_session(self, session_id):

        try:
            if session_id:
                return await sync_to_async(ChatSession.objects.get)(id=session_id)
        except ChatSession.DoesNotExist:
            pass

        kwargs = {"title": "New Chat Session"}

        if not isinstance(self.user, AnonymousUser):
            kwargs["user"] = self.user

        return await sync_to_async(ChatSession.objects.create)(**kwargs)