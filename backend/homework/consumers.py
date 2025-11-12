# backend/homework/consumers.py
import logging
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from urllib.parse import parse_qs

from .models import Homework
from .utils import evaluate_homework_with_ai
from progress.utils import update_progress_on_homework

logger = logging.getLogger(__name__)

class HomeworkConsumer(AsyncJsonWebsocketConsumer):
    """
    WS for homework submission & AI evaluation (keeps REST intact).
    Payload:
      {"subject":"Mathematics","text_content":"..."}  # file upload not supported via WS
    Emits:
      {"type":"status","value":"processing"}
      {"type":"final","homework_id":1,"feedback":"...","score":78.5}
      {"type":"error","message":"..."}
    """

    async def connect(self):
        self.user = await self._get_user_from_token()
        await self.accept()
        uname = getattr(self.user, "username", "AnonymousUser")
        logger.info(f"✅ WS(Homework) connected: {uname}")
        await self.send_json({"message": "Connected to Homework WS"})

    async def receive_json(self, content, **kwargs):
        try:
            subject = (content.get("subject") or "").strip()
            text_content = (content.get("text_content") or "").strip()

            if not subject or not text_content:
                await self.send_json({"type": "error", "message": "subject and text_content are required"})
                return

            await self.send_json({"type": "status", "value": "processing"})

            result = await sync_to_async(evaluate_homework_with_ai)(
                getattr(self.user, "id", None), text_content, subject
            )
            feedback = result.get("feedback", "")
            score = float(result.get("score", 0.0))

            homework = None
            if not isinstance(self.user, AnonymousUser):
                homework = await sync_to_async(Homework.objects.create)(
                    student=self.user,
                    subject=subject,
                    text_content=text_content,
                    ai_feedback=feedback,
                    score=score,
                )
                try:
                    await sync_to_async(update_progress_on_homework)(self.user, subject, score)
                except Exception as e:
                    logger.warning(f"Progress update failed (homework WS): {e}")

            await self.send_json({
                "type": "final",
                "homework_id": getattr(homework, "id", None),
                "feedback": feedback,
                "score": score,
            })
        except Exception as e:
            logger.exception("Homework WS internal error")
            await self.send_json({"type": "error", "message": str(e)})

    async def disconnect(self, close_code):
        uname = getattr(self.user, "username", "AnonymousUser")
        logger.info(f"🔌 WS(Homework) disconnected ({close_code}): {uname}")

    async def _get_user_from_token(self):
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
        except Exception:
            return AnonymousUser()