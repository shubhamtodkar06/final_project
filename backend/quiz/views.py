from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from core.ai_manager import ai_generate
from progress.utils import update_progress_on_quiz
from .models import Quiz
import json


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .quiz_engine import generate_proactive_quiz
from .models import Quiz
import json
import re
import logging


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_quiz(request):

    student = request.user

    filters = request.data.get("filters", {})
    include_suggestions = request.data.get("include_suggestions", True)

    logging.info(f"🎯 Proactive Quiz | student={student.id} | filters={filters}")

    try:
        ai_output, final_topics, suggestions = generate_proactive_quiz(
            student,
            filters,
            include_suggestions
        )
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    # ⭐ Robust JSON extraction
    cleaned = re.sub(r"```(?:json)?|```", "", ai_output).strip()

    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)

    if json_match:
        cleaned = json_match.group(0)

    try:
        data = json.loads(cleaned)
    except Exception as e:
        logging.warning(f"Quiz JSON parse failed: {e}")
        data = {}

    questions = data.get("questions", [])

    if not questions:
        questions = [{
            "q": "AI could not generate quiz.",
            "options": [],
            "correct": None
        }]

    quiz = Quiz.objects.create(
        student=student,
        subject=filters.get("subjects", ["General"])[0],
        topics=final_topics,
        strategy_used="proactive",
        questions=questions
    )

    return Response({
        "quiz_id": quiz.id,
        "questions": questions,
        "final_topics": final_topics,
        "suggestions": suggestions,
        "suggestion_used": include_suggestions
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_quiz(request, quiz_id):
    """Submit answers and evaluate using AI feedback."""
    import logging
    import traceback
    try:
        quiz = Quiz.objects.get(id=quiz_id, student=request.user)
        logging.info(f"📝 Submitting quiz for user={request.user.id}, quiz_id={quiz_id}")
        print(f"[DEBUG] submit_quiz: user_id={request.user.id}, quiz_id={quiz_id}")
    except Quiz.DoesNotExist:
        logging.warning(f"⚠️ Quiz not found: id={quiz_id}, user={request.user.id}")
        print(f"[DEBUG] Quiz not found: id={quiz_id}, user={request.user.id}")
        return Response({"error": "Quiz not found"}, status=404)

    student_answers = request.data.get("answers", [])
    quiz.student_answers = student_answers

    correct_count = 0
    total = len(quiz.questions)
    correct_topics, wrong_topics = [], []

    for i, q in enumerate(quiz.questions):
        correct = q.get("correct")
        topic = q.get("topic", "General")
        if i < len(student_answers) and student_answers[i] == correct:
            correct_count += 1
            correct_topics.append(topic)
        else:
            wrong_topics.append(topic)

    quiz.score = (correct_count / total) * 100 if total else 0

    try:
        feedback = ai_generate(
            request.user.id,
            f"Provide quiz feedback. Correct: {correct_topics}, Wrong: {wrong_topics}",
            mode="report",
            subject=quiz.subject,
        )
        logging.info(f"🧠 Quiz AI feedback (truncated): {str(feedback)[:300]}")
        print(f"[DEBUG] AI feedback for quiz (truncated): {str(feedback)[:100]}")
    except Exception as e:
        logging.error(f"❌ Quiz AI feedback generation failed: {e}\n{traceback.format_exc()}")
        print(f"[DEBUG] Quiz AI feedback generation failed: {e}")
        feedback = "AI feedback unavailable. Please try again later."

    quiz.ai_feedback = feedback
    try:
        quiz.save()
        logging.info(f"✅ Quiz saved with score={quiz.score}")
        print(f"[DEBUG] Quiz saved with score={quiz.score}")
    except Exception as e:
        logging.error(f"❌ Failed to save quiz after feedback: {e}\n{traceback.format_exc()}")
        print(f"[DEBUG] Failed to save quiz after feedback: {e}")

    try:
        update_progress_on_quiz(request.user, quiz.subject, correct_topics, wrong_topics)
        logging.info(f"📈 Progress updated for user={request.user.id}, subject={quiz.subject}")
        print(f"[DEBUG] Progress updated for user={request.user.id}, subject={quiz.subject}")
    except Exception as e:
        logging.warning(f"⚠️ Failed to update progress after quiz: {e}")
        print(f"[DEBUG] Failed to update progress after quiz: {e}")

    return Response(
        {
            "score": quiz.score,
            "feedback": feedback,
            "correct": correct_topics,
            "wrong": wrong_topics,
        },
        status=status.HTTP_200_OK,
    )