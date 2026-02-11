import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Homework
from .utils import clean_json_response, normalize_score, extract_text_from_file
from .homework_engine import evaluate_proactive_homework
from progress.utils import update_progress_on_homework

logger = logging.getLogger(__name__)


class SubmitHomeworkView(APIView):
    """
    Proactive Homework Evaluation

    ✔ Filter Based
    ✔ Uses Weak / Strong Topics
    ✔ Uses RAG
    ✔ Updates Topic Mastery
    ✔ Suggests Additional Topics
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):

        user = request.user
        subject = request.data.get("subject")
        text_content = request.data.get("text_content")
        file = request.FILES.get("file")
        # -------------------------
        # Safe Filters Handling
        # -------------------------
        filters = request.data.get("filters")

        # If no filters provided, default to subject
        if not filters:
            filters = {"subjects": [subject]}

        # If filters come as string (form-data case), parse safely
        elif isinstance(filters, str):
            import json
            try:
                filters = json.loads(filters)
            except Exception:
                logger.warning("⚠️ Filters received as invalid JSON string. Falling back to subject-only filter.")
                filters = {"subjects": [subject]}

        # Ensure filters is always dict
        if not isinstance(filters, dict):
            logger.warning("⚠️ Filters not a dictionary. Resetting to subject-only filter.")
            filters = {"subjects": [subject]}

        if not subject:
            return Response(
                {"error": "Subject required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # =========================
        # Extract Homework Text (Enhanced + Logging)
        # =========================
        if text_content:
            logger.info(f"📘 Homework submission using text_content | user={user.id} | subject={subject}")
            extracted_text = text_content.strip()

            if not extracted_text:
                logger.warning("⚠️ text_content provided but empty after strip()")
                return Response(
                    {"error": "text_content is empty."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        elif file:
            logger.info(
                f"📂 Homework submission using file | "
                f"user={user.id} | subject={subject} | "
                f"filename={file.name} | content_type={getattr(file, 'content_type', None)}"
            )

            try:
                extracted_text = extract_text_from_file(file)

                if not extracted_text:
                    logger.warning(
                        f"⚠️ File extraction returned empty text | filename={file.name}"
                    )
                    return Response(
                        {"error": "Could not extract text from file."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            except Exception as e:
                logger.error(f"❌ File text extraction failed: {e}")
                return Response(
                    {"error": "File text extraction failed"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            logger.warning(
                f"⚠️ Homework submission missing both text_content and file | user={user.id}"
            )
            return Response(
                {"error": "Provide text_content or file"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # =========================
        # Proactive AI Evaluation (Robust & Safe)
        # =========================

        try:
            ai_raw, final_topics, suggestions = evaluate_proactive_homework(
                user,
                filters,
                extracted_text
            )

            logger.info(
                f"🤖 AI evaluation completed | user={user.id} | "
                f"topics={final_topics}"
            )

            if not ai_raw:
                raise ValueError("Empty AI response")

            # Ensure string format before cleaning
            if not isinstance(ai_raw, str):
                ai_raw = str(ai_raw)

            cleaned = clean_json_response(ai_raw)

            # --- Case 1: Proper JSON dict ---
            if isinstance(cleaned, dict):
                feedback = cleaned.get("feedback", "No feedback generated.")
                score = normalize_score(cleaned.get("score", 0))

            # --- Case 2: JSON returned as string ---
            elif isinstance(cleaned, str):
                try:
                    import json
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, dict):
                        feedback = parsed.get("feedback", "No feedback generated.")
                        score = normalize_score(parsed.get("score", 0))
                    else:
                        feedback = cleaned
                        score = 0.0
                except Exception:
                    feedback = cleaned
                    score = 0.0

            # --- Case 3: Unexpected type ---
            else:
                logger.warning("⚠️ Unexpected AI response format. Using fallback.")
                feedback = str(cleaned)
                score = 0.0

        except Exception as e:
            logger.error(f"❌ AI Homework Failed: {e}", exc_info=True)
            return Response(
                {"error": "AI evaluation failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # =========================
        # Save Homework
        # =========================

        homework = Homework.objects.create(
            student=user,
            subject=subject,
            text_content=extracted_text,
            ai_feedback=feedback,
            score=score,
        )

        # =========================
        # Update Progress + Mastery
        # =========================

        try:
            topic_name = final_topics[0] if final_topics else None

            update_progress_on_homework(
                user,
                subject,
                score,
                topic_name
            )

        except Exception as e:
            logger.warning(f"Progress update failed: {e}")

        # =========================
        # Response
        # =========================

        return Response({
            "message": "Homework submitted successfully",
            "homework_id": homework.id,
            "feedback": feedback,
            "score": score,
            "topics_used": final_topics,
            "suggestions": suggestions
        }, status=status.HTTP_201_CREATED)