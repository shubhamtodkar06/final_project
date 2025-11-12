#backend/homework/views.py
from django.shortcuts import render

# Create your views here.

#backend/homework/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Homework
from .utils import evaluate_homework_with_ai
from progress.utils import update_progress_on_homework
from django.core.files.uploadedfile import UploadedFile

class SubmitHomeworkView(APIView):
    """
    Handles homework submission via text or file. Evaluates with AI and persists feedback and score.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        subject = request.data.get("subject")
        text_content = request.data.get("text_content")
        file = request.FILES.get("file")

        if not subject:
            return Response({"error": "Subject is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Extract text: either from text_content or from file (simulate OCR if file)
        if text_content:
            extracted_text = text_content
        elif file:
            # Simulate OCR: for now, just decode if it's a text file, else placeholder
            if isinstance(file, UploadedFile) and file.content_type.startswith("text"):
                try:
                    extracted_text = file.read().decode("utf-8")
                except Exception:
                    extracted_text = "[Could not decode file as text.]"
            else:
                extracted_text = "[OCR Placeholder: Text extraction from file not implemented.]"
        else:
            return Response({"error": "No homework content provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Evaluate with AI
        ai_result = evaluate_homework_with_ai(user.id, extracted_text, subject)
        ai_feedback = ai_result.get("feedback", "")
        score = ai_result.get("score", 0)

        # Save Homework instance
        homework = Homework.objects.create(
            student=user,
            subject=subject,
            text_content=extracted_text,
            ai_feedback=ai_feedback,
            score=score,
        )

        # Update progress
        update_progress_on_homework(user, subject, score)

        return Response(
            {
                "message": "Homework submitted and evaluated.",
                "homework_id": homework.id,
                "feedback": ai_feedback,
                "score": score,
            },
            status=status.HTTP_201_CREATED,
        )