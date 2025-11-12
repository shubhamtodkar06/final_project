# backend/homework/views.py
import re
import json
import logging
from django.core.files.uploadedfile import UploadedFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Homework
from .utils import evaluate_homework_with_ai
from progress.utils import update_progress_on_homework

logger = logging.getLogger(__name__)

class SubmitHomeworkView(APIView):
    """
    Handles homework submission (text or file).
    Evaluates using AI → Stores feedback → Updates progress.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import traceback
        user = request.user
        subject = request.data.get("subject")
        text_content = request.data.get("text_content")
        file = request.FILES.get("file")

        logger.info(f"📥 Homework POST incoming | user_id={getattr(user, 'id', None)} | username={getattr(user, 'username', None)} | data={request.data}")
        print(f"[DEBUG] SubmitHomeworkView.post called for user={user.id} with data={request.data}")

        if not subject:
            logger.warning("❗ Homework submission missing subject")
            return Response({"error": "Subject is required."}, status=status.HTTP_400_BAD_REQUEST)

        # === Extract Text from Input ===
        if text_content:
            extracted_text = text_content.strip()
        elif file:
            if isinstance(file, UploadedFile) and file.content_type.startswith("text"):
                try:
                    extracted_text = file.read().decode("utf-8")
                except Exception as e:
                    logger.warning(f"⚠️ Could not decode uploaded file: {e}")
                    print(f"[DEBUG] Could not decode uploaded file: {e}")
                    extracted_text = "[Error decoding file]"
            else:
                logger.warning("⚠️ Uploaded file is not text; OCR not implemented.")
                print("[DEBUG] Uploaded file is not text; OCR not implemented.")
                extracted_text = "[OCR Placeholder: Text extraction not implemented yet.]"
        else:
            logger.warning("❗ No homework content provided.")
            return Response({"error": "No homework content provided."}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"📘 Homework submission received | student={user.id}, subject={subject}")
        print(f"[DEBUG] Homework submission received | student={user.id}, subject={subject}")

        # === Evaluate using AI ===
        try:
            ai_result_raw = evaluate_homework_with_ai(user.id, extracted_text, subject)
            logger.debug(f"🧠 Raw AI result: {str(ai_result_raw)[:300]}")
            print(f"[DEBUG] Raw AI result (truncated): {str(ai_result_raw)[:100]}")

            # Some models may return stringified JSON or markdown-wrapped JSON
            if isinstance(ai_result_raw, str):
                clean_text = re.sub(r"^```json|```$", "", ai_result_raw.strip(), flags=re.MULTILINE).strip()
                try:
                    ai_result = json.loads(clean_text)
                except json.JSONDecodeError:
                    logger.warning("⚠️ Could not parse AI JSON. Using raw text fallback.")
                    print("[DEBUG] Could not parse AI JSON. Using raw text fallback.")
                    ai_result = {"feedback": clean_text, "score": 0.0}
            else:
                ai_result = ai_result_raw

            feedback_text = ai_result.get("feedback", "No feedback available.")
            score_value = float(ai_result.get("score", 0.0))

        except Exception as e:
            logger.error(f"❌ AI evaluation failed: {e}\n{traceback.format_exc()}")
            print(f"[DEBUG] AI evaluation failed: {e}")
            feedback_text = "AI evaluation failed. Please try again later."
            score_value = 0.0

        # === Save Homework Record ===
        try:
            homework = Homework.objects.create(
                student=user,
                subject=subject,
                text_content=extracted_text,
                ai_feedback=feedback_text,
                score=score_value,
            )
            logger.info(f"✅ Homework record saved | ID={homework.id}, Score={score_value}")
            print(f"[DEBUG] Homework record saved | ID={homework.id}, Score={score_value}")
        except Exception as e:
            logger.error(f"❌ Failed to save homework: {e}\n{traceback.format_exc()}")
            print(f"[DEBUG] Failed to save homework: {e}")
            return Response({"error": "Failed to save homework."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # === Update Progress ===
        try:
            update_progress_on_homework(user, subject, score_value)
            logger.info(f"📈 Progress updated for user={user.id}, subject={subject}")
            print(f"[DEBUG] Progress updated for user={user.id}, subject={subject}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to update progress: {e}")
            print(f"[DEBUG] Failed to update progress: {e}")

        logger.info(f"✅ Homework processed | ID={homework.id}, Score={score_value}")
        print(f"[DEBUG] Homework processed | ID={homework.id}, Score={score_value}")

        return Response(
            {
                "message": "Homework submitted and evaluated.",
                "homework_id": homework.id,
                "feedback": feedback_text,
                "score": score_value,
            },
            status=status.HTTP_201_CREATED,
        )