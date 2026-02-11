# backend/reports/views.py

from django.conf import settings
from django.core.mail import send_mail

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from progress.models import Progress
from core.ai_manager import ai_generate


class WeeklyReportView(APIView):
    """
    Generate a weekly AI report summarizing student's progress.
    Used for student dashboard preview.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        progress_qs = Progress.objects.filter(student=user)

        if not progress_qs.exists():
            return Response(
                {"message": "No progress data available."},
                status=status.HTTP_200_OK
            )

        context = ""
        for p in progress_qs:
            context += (
                f"Subject: {p.subject}\n"
                f"Average Score: {p.average_score}\n"
                f"Completion Rate: {p.completion_rate}\n"
                f"Weak Topics: {p.weak_topics}\n"
                f"Strong Topics: {p.strong_topics}\n\n"
            )

        ai_summary = ai_generate(
            student_id=user.id,
            query=f"Summarize weekly academic progress and suggest improvements:\n{context}",
            mode="report"
        )

        return Response(
            {
                "student": user.username,
                "summary": ai_summary,
            },
            status=status.HTTP_200_OK
        )


class SendParentReportView(APIView):
    """
    Sends an AI-generated analytical progress report to parent's email.
    Triggered via frontend button.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        parent_email = request.data.get("parent_email")

        if not parent_email:
            return Response(
                {"error": "parent_email is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        progress_qs = Progress.objects.filter(student=user)
        if not progress_qs.exists():
            return Response(
                {"error": "No progress data available."},
                status=status.HTTP_400_BAD_REQUEST
            )

        context = ""
        for p in progress_qs:
            context += (
                f"Subject: {p.subject}\n"
                f"Average Score: {p.average_score}\n"
                f"Completion Rate: {p.completion_rate}\n"
                f"Weak Topics: {p.weak_topics}\n"
                f"Strong Topics: {p.strong_topics}\n\n"
            )

        try:
            ai_summary = ai_generate(
                student_id=user.id,
                query=(
                    "Generate a clear, parent-friendly academic progress report "
                    "with improvement suggestions:\n" + context
                ),
                mode="report"
            )
        except Exception:
            ai_summary = (
                "We encountered an issue generating the AI report. "
                "Please review the progress data manually."
            )

        subject = f"Weekly Academic Progress Report – {user.get_full_name() or user.username}"

        email_body = f"""
Dear Parent,

Here is the academic progress summary for your child, {user.get_full_name() or user.username}.

{ai_summary}

This report is generated automatically using an AI-powered personalized learning system.

Regards,
AI-Powered Personalized Learning Platform
"""

        try:
            send_mail(
                subject=subject,
                message=email_body,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[parent_email],
                fail_silently=False,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to send email: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"message": "Parent report sent successfully."},
            status=status.HTTP_200_OK
        )