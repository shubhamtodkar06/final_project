# backend/quiz/consumers.py
import json
import logging
import re
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

from core.ai_manager import ai_generate
from .models import Quiz
from progress.utils import update_progress_on_quiz

logger = logging.getLogger(__name__)

class QuizConsumer(AsyncJsonWebsocketConsumer):
    """
    WS for quiz generate/submit (REST remains available).
    Generate payload:
      {"action":"generate","subject":"Math","topic":"Fractions"}
    Submit payload:
      {"action":"submit","quiz_id": 12, "answers": ["A","B","C","D"]}
    Emits status/final/error events.
    """

    async def connect(self):
        self.user = await self._get_user_from_token()
        await self.accept()
        uname = getattr(self.user, "username", "AnonymousUser")
        logger.info(f"✅ WS(Quiz) connected: {uname}")
        await self.send_json({"message": "Connected to Quiz WS"})

    async def receive_json(self, content, **kwargs):
        action = (content.get("action") or "").lower()
        if action == "generate":
            await self._handle_generate(content)
        elif action == "submit":
            await self._handle_submit(content)
        else:
            await self.send_json({"type": "error", "message": "Unknown action. Use 'generate' or 'submit'."})

    async def _handle_generate(self, content):
        subject = content.get("subject")
        topic = content.get("topic", "General knowledge")
        await self.send_json({"type": "status", "value": "generating"})
        try:
            ai_output = await sync_to_async(ai_generate)(
                getattr(self.user, "id", None), topic, mode="quiz", subject=subject
            )
            clean_output = re.sub(r"^```json|```$", "", (ai_output or "").strip(), flags=re.MULTILINE).strip()
            try:
                data = json.loads(clean_output)
            except json.JSONDecodeError:
                data = {}

            questions = data.get("questions", []) if isinstance(data, dict) else []
            if not questions:
                # fallback to extract question-like lines
                questions = []
                for line in (ai_output or "").split("\n"):
                    if "?" in line:
                        questions.append({"q": line.strip().strip("-* "), "options": [], "correct": None})

            # normalize
            norm = []
            for q in questions:
                if isinstance(q, dict) and "q" in q:
                    q.setdefault("options", [])
                    q.setdefault("correct", None)
                    norm.append(q)

            quiz = None
            if not isinstance(self.user, AnonymousUser):
                quiz = await sync_to_async(Quiz.objects.create)(
                    student=self.user, subject=subject, questions=norm
                )

            await self.send_json({
                "type": "final",
                "quiz_id": getattr(quiz, "id", None),
                "questions": norm,
            })
        except Exception as e:
            logger.exception("Quiz generate failed")
            await self.send_json({"type": "error", "message": str(e)})

    async def _handle_submit(self, content):
        try:
            quiz_id = content.get("quiz_id")
            answers = content.get("answers", [])
            if not quiz_id:
                await self.send_json({"type": "error", "message": "quiz_id is required"})
                return

            await self.send_json({"type": "status", "value": "scoring"})

            quiz = await sync_to_async(Quiz.objects.get)(id=quiz_id)
            if not isinstance(self.user, AnonymousUser) and quiz.student_id != self.user.id:
                await self.send_json({"type": "error", "message": "Not authorized for this quiz."})
                return

            quiz.student_answers = answers
            correct_count = 0
            total = len(quiz.questions)
            correct_topics, wrong_topics = [], []

            for i, q in enumerate(quiz.questions):
                correct = q.get("correct")
                topic = q.get("topic", "General")
                if i < len(answers) and answers[i] == correct:
                    correct_count += 1
                    correct_topics.append(topic)
                else:
                    wrong_topics.append(topic)

            quiz.score = (correct_count / total) * 100 if total else 0

            # Optional AI feedback
            try:
                feedback = await sync_to_async(ai_generate)(
                    getattr(self.user, "id", None),
                    f"Provide quiz feedback. Correct: {correct_topics}, Wrong: {wrong_topics}",
                    mode="report",
                    subject=quiz.subject,
                )
            except Exception:
                feedback = "AI feedback unavailable."

            quiz.ai_feedback = feedback
            await sync_to_async(quiz.save)()

            if not isinstance(self.user, AnonymousUser):
                try:
                    await sync_to_async(update_progress_on_quiz)(
                        self.user, quiz.subject, correct_topics, wrong_topics
                    )
                except Exception as e:
                    logger.warning(f"Progress update failed (quiz WS): {e}")

            await self.send_json({
                "type": "final",
                "score": quiz.score,
                "feedback": quiz.ai_feedback,
                "correct": correct_topics,
                "wrong": wrong_topics,
            })
        except Quiz.DoesNotExist:
            await self.send_json({"type": "error", "message": "Quiz not found"})
        except Exception as e:
            logger.exception("Quiz submit failed")
            await self.send_json({"type": "error", "message": str(e)})

    async def disconnect(self, close_code):
        uname = getattr(self.user, "username", "AnonymousUser")
        logger.info(f"🔌 WS(Quiz) disconnected ({close_code}): {uname}")

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