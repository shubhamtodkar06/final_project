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
    """Generate quiz based on weak topics or subject."""
    student = request.user
    subject = request.data.get("subject")
    query = request.data.get("topic", "Generate quiz")

    result = ai_generate(student.id, query, mode="quiz", subject=subject)

    try:
        data = json.loads(result)
    except Exception:
        data = {"questions": [], "answers": [], "error": "Invalid AI format"}

    quiz = Quiz.objects.create(
        student=student,
        subject=subject,
        questions=data.get("questions", []),
    )

    return Response(
        {"quiz_id": quiz.id, "questions": data.get("questions")},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_quiz(request, quiz_id):
    """Submit answers and evaluate using AI feedback."""
    try:
        quiz = Quiz.objects.get(id=quiz_id, student=request.user)
    except Quiz.DoesNotExist:
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

    feedback = ai_generate(
        request.user.id,
        f"Provide quiz feedback. Correct: {correct_topics}, Wrong: {wrong_topics}",
        mode="report",
        subject=quiz.subject,
    )

    quiz.ai_feedback = feedback
    quiz.save()

    update_progress_on_quiz(request.user, quiz.subject, correct_topics, wrong_topics)

    return Response(
        {
            "score": quiz.score,
            "feedback": feedback,
            "correct": correct_topics,
            "wrong": wrong_topics,
        },
        status=status.HTTP_200_OK,
    )