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
        filters = request.data.get("filters", {"subjects": [subject]})

        if not subject:
            return Response(
                {"error": "Subject required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # =========================
        # Extract Homework Text
        # =========================

        if text_content:
            extracted_text = text_content.strip()

        elif file:
            try:
                extracted_text = extract_text_from_file(file)
            except Exception as e:
                return Response(
                    {"error": "File text extraction failed"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"error": "Provide text_content or file"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # =========================
        # Proactive AI Evaluation
        # =========================

        try:

            ai_raw, final_topics, suggestions = evaluate_proactive_homework(
                user,
                filters,
                extracted_text
            )

            cleaned = clean_json_response(ai_raw)

            feedback = cleaned.get("feedback")
            score = normalize_score(cleaned.get("score"))

        except Exception as e:
            logger.error(f"AI Homework Failed: {e}")

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