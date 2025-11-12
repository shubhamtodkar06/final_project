#backend/quiz/views.py
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_quiz(request):
    """Generate quiz based on weak topics or subject with robust JSON parsing."""
    import re
    import logging
    import traceback
    student = request.user
    subject = request.data.get("subject")
    topic = request.data.get("topic", "General knowledge")

    logging.info(f"🎯 Generating quiz for student={student.id}, subject={subject}, topic={topic}")
    print(f"[DEBUG] generate_quiz: user_id={student.id}, subject={subject}, topic={topic}")

    # Call AI model
    try:
        ai_output = ai_generate(student.id, topic, mode="quiz", subject=subject)
        logging.info(f"🧠 Raw AI response (truncated): {str(ai_output)[:300]}")
        print(f"[DEBUG] AI quiz output (truncated): {str(ai_output)[:100]}")
    except Exception as e:
        logging.error(f"❌ AI quiz generation failed: {e}\n{traceback.format_exc()}")
        print(f"[DEBUG] AI quiz generation failed: {e}")
        return Response({"error": "AI quiz generation failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Clean AI output (remove markdown, code fences, etc.)
    clean_output = re.sub(r"^```json|```$", "", ai_output.strip(), flags=re.MULTILINE).strip()

    # Try parsing JSON safely
    try:
        data = json.loads(clean_output)
    except json.JSONDecodeError:
        logging.warning("⚠️ AI response not valid JSON. Attempting manual recovery.")
        print("[DEBUG] AI response not valid JSON. Attempting manual recovery.")
        data = {}

    # Validate structure
    questions = data.get("questions", []) if isinstance(data, dict) else []
    if not questions or not isinstance(questions, list):
        logging.warning("⚠️ No questions found — fallback to manual extraction.")
        print("[DEBUG] No questions found — fallback to manual extraction.")
        questions = []
        for line in ai_output.split("\n"):
            if "?" in line:
                questions.append({
                    "q": line.strip().replace("*", "").replace("-", ""),
                    "options": [],
                    "correct": None
                })

    # Ensure each question has options and correct answer
    valid_questions = []
    for q in questions:
        if isinstance(q, dict) and "q" in q:
            q.setdefault("options", [])
            q.setdefault("correct", None)
            valid_questions.append(q)

    if not valid_questions:
        logging.warning("⚠️ No valid questions parsed from AI or fallback.")
        print("[DEBUG] No valid questions parsed from AI or fallback.")
        valid_questions = [{
            "q": "AI failed to generate quiz. Please retry later.",
            "options": [],
            "correct": None
        }]

    # Save quiz
    try:
        quiz = Quiz.objects.create(student=student, subject=subject, questions=valid_questions)
        logging.info(f"✅ Quiz created: ID={quiz.id}, {len(valid_questions)} questions generated.")
        print(f"[DEBUG] Quiz saved: ID={quiz.id}, questions={len(valid_questions)}")
    except Exception as e:
        logging.error(f"❌ Failed to save quiz: {e}\n{traceback.format_exc()}")
        print(f"[DEBUG] Failed to save quiz: {e}")
        return Response({"error": "Failed to save quiz."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        {"quiz_id": quiz.id, "questions": valid_questions},
        status=status.HTTP_201_CREATED
    )

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