#backend/reports/views.py

# backend/reports/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from progress.models import Progress
from core.ai_manager import ai_generate

class WeeklyReportView(APIView):
    """
    Generate weekly AI report summarizing student's progress and suggesting improvement.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        progress_data = Progress.objects.filter(student=user)
        summary_context = ""
        for p in progress_data:
            summary_context += f"Subject: {p.subject}, Avg: {p.average_score}, Weak: {p.weak_topics}, Strong: {p.strong_topics}\n"

        ai_summary = ai_generate(user.id, f"Summarize progress and suggest improvements:\n{summary_context}", mode="report")
        return Response({
            "student": user.username,
            "summary": ai_summary,
            "context_used": summary_context,
        }, status=status.HTTP_200_OK)
