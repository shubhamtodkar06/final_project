# backend/progress/views.py

from statistics import mean
from datetime import timedelta

from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Progress, StudentTopicProgress
from .serializers import ProgressSerializer


# ======================================================
# BASIC CRUD
# ======================================================

class ProgressListView(generics.ListAPIView):
    """
    List all progress records for the logged-in student.
    """
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Progress.objects.filter(student=self.request.user)


class ProgressUpdateView(generics.UpdateAPIView):
    """
    Update progress manually (restricted to own records).
    """
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return Progress.objects.filter(student=self.request.user)


# ======================================================
# OVERVIEW (GLOBAL DASHBOARD)
# ======================================================

class ProgressOverviewView(APIView):
    """
    Overall progress summary across all subjects.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Progress.objects.filter(student=request.user)

        if not qs.exists():
            return Response(
                {"message": "No progress data available."},
                status=status.HTTP_200_OK
            )

        avg_scores = [p.average_score for p in qs]
        completion_rates = [p.completion_rate for p in qs]

        subjects = []
        for p in qs:
            subjects.append({
                "subject": p.subject,
                "average_score": p.average_score,
                "completion_rate": p.completion_rate,
                "weak_topics": p.weak_topics,
                "strong_topics": p.strong_topics,
            })

        return Response({
            "average_score": round(mean(avg_scores), 2),
            "completion_rate": round(mean(completion_rates), 2),
            "subjects": subjects,
        })


# ======================================================
# SUBJECT-SPECIFIC ANALYTICS
# ======================================================

class ProgressSubjectView(APIView):
    """
    Detailed analytics for a single subject.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, subject):
        progress = get_object_or_404(
            Progress,
            student=request.user,
            subject__iexact=subject
        )

        return Response({
            "subject": progress.subject,
            "average_score": progress.average_score,
            "completion_rate": progress.completion_rate,
            "weak_topics": progress.weak_topics,
            "strong_topics": progress.strong_topics,
        })


# ======================================================
# TREND ANALYSIS
# ======================================================

class ProgressTrendView(APIView):
    """
    Weekly progress trend (simple simulation).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Progress.objects.filter(student=request.user)

        if not qs.exists():
            return Response(
                {"message": "No progress data available."},
                status=status.HTTP_200_OK
            )

        today = timezone.now().date()
        avg_score = mean([p.average_score for p in qs])

        trend = []
        for i in range(6, -1, -1):
            week_date = today - timedelta(days=i * 7)
            trend.append({
                "week": week_date.strftime("%Y-%m-%d"),
                "average_score": round(avg_score, 2),
            })

        return Response(trend)


# ======================================================
# DASHBOARD ANALYTICS (CARDS)
# ======================================================

class ProgressAnalyticsView(APIView):
    """
    High-level analytics for dashboard cards.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Progress.objects.filter(student=request.user)

        if not qs.exists():
            return Response(
                {"message": "No analytics available."},
                status=status.HTTP_200_OK
            )

        weak_topics = set()
        strong_topics = set()

        for p in qs:
            weak_topics.update(p.weak_topics or [])
            strong_topics.update(p.strong_topics or [])

        return Response({
            "total_subjects": qs.count(),
            "average_score": round(mean([p.average_score for p in qs]), 2),
            "completion_rate": round(mean([p.completion_rate for p in qs]), 2),
            "weak_topics": sorted(list(weak_topics)),
            "strong_topics": sorted(list(strong_topics)),
        })


# ======================================================
# DEEP INSIGHTS (AI / REPORTS)
# ======================================================

class ProgressDeepInsightsView(APIView):
    """
    Advanced analytics for AI reports and parent summaries.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Progress.objects.filter(student=request.user)

        if not qs.exists():
            return Response(
                {"message": "No deep insights available."},
                status=status.HTTP_200_OK
            )

        insights = []
        for p in qs:
            if p.average_score < 40:
                readiness = "Needs Attention"
            elif p.average_score < 70:
                readiness = "Average"
            else:
                readiness = "Good"

            insights.append({
                "subject": p.subject,
                "readiness_level": readiness,
                "average_score": p.average_score,
                "weak_topics": p.weak_topics,
                "strong_topics": p.strong_topics,
            })

        return Response({"insights": insights})
    from .models import StudentTopicProgress


class LearningPathView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        topics = StudentTopicProgress.objects.filter(
            student=request.user
        ).select_related("topic", "topic__subject")

        data = []

        for t in topics:
            data.append({
                "subject": t.topic.subject.name,
                "topic": t.topic.name,
                "status": t.status,
                "mastery_score": t.mastery_score
            })

        return Response(data)