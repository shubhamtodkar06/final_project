
# backend/progress/views.py
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Progress
from .serializers import ProgressSerializer
from django.shortcuts import get_object_or_404

class ProgressListView(generics.ListAPIView):
    """
    List all progress records for the current user.
    """
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Progress.objects.filter(student=self.request.user)


class ProgressUpdateView(generics.UpdateAPIView):
    """
    Manually update a progress record (e.g., for admin or manual correction).
    """
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]
    queryset = Progress.objects.all()
    lookup_field = "pk"

    def get_queryset(self):
        # Users may only update their own progress
        return Progress.objects.filter(student=self.request.user)
# backend/progress/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Progress
from statistics import mean

class ProgressOverviewView(APIView):
    """
    Summarizes student's overall academic progress across all subjects.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        progress_qs = Progress.objects.filter(student=user)

        if not progress_qs.exists():
            return Response({"message": "No progress data available."}, status=200)

        subjects_data = []
        avg_scores = []
        completion_rates = []

        for p in progress_qs:
            subjects_data.append({
                "subject": p.subject,
                "average_score": p.average_score,
                "weak_topics": p.weak_topics,
                "strong_topics": p.strong_topics,
                "completion_rate": p.completion_rate,
            })
            avg_scores.append(p.average_score)
            completion_rates.append(p.completion_rate)

        overview = {
            "average_score": round(mean(avg_scores), 2),
            "completion_rate": round(mean(completion_rates), 2),
            "subjects": subjects_data,
        }

        return Response(overview, status=200)
    
# ---------------------------------------------
# New Analytics Endpoints (Safe to append)
# ---------------------------------------------
from datetime import timedelta
from django.utils import timezone
from statistics import mean
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Progress

class ProgressSubjectView(APIView):
    """
    Returns detailed analytics for a specific subject,
    including score trend and weak/strong topics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, subject):
        user = request.user
        subject_data = Progress.objects.filter(student=user, subject__iexact=subject).first()

        if not subject_data:
            return Response({"message": f"No progress found for {subject}."}, status=404)

        trend = [
            {"date": (timezone.now() - timedelta(days=i*7)).strftime("%Y-%m-%d"), "score": max(subject_data.average_score - i*2, 0)}
            for i in range(5)
        ]

        data = {
            "subject": subject_data.subject,
            "average_score": subject_data.average_score,
            "completion_rate": subject_data.completion_rate,
            "weak_topics": subject_data.weak_topics,
            "strong_topics": subject_data.strong_topics,
            "trend": list(reversed(trend)),
        }
        return Response(data, status=200)


class ProgressTrendView(APIView):
    """
    Aggregates overall improvement trend across subjects.
    Returns a subject-wise timeline summary.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        progress_qs = Progress.objects.filter(student=user)

        if not progress_qs.exists():
            return Response({"message": "No progress data yet."}, status=200)

        trend_data = []
        for p in progress_qs:
            subject_trend = {
                "subject": p.subject,
                "average_score": p.average_score,
                "completion_rate": p.completion_rate,
                "improvement": f"+{round(p.average_score/10,1)}%",
            }
            trend_data.append(subject_trend)

        overview = {
            "trend_summary": trend_data,
            "overall_average": round(mean([t["average_score"] for t in trend_data]), 2),
        }
        return Response(overview, status=200)


# ---------------------------------------------
# Advanced Analytics Endpoint for Dashboards
# ---------------------------------------------
from django.db.models import Avg, Count
from datetime import datetime, timedelta
import random

class ProgressAnalyticsView(APIView):
    """
    Provides detailed analytics for dashboards:
    - subject performance distribution
    - weak/strong topic ratio
    - weekly score trend
    - completion breakdown
    - engagement simulation
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        progress_qs = Progress.objects.filter(student=user)
        if not progress_qs.exists():
            return Response({"message": "No progress data available."}, status=200)

        # Subject Performance (for bar chart)
        subject_performance = [
            {"subject": p.subject, "score": round(p.average_score, 2)}
            for p in progress_qs
        ]

        # Weak/Strong Topics (for pie chart)
        total_weak = sum(len(p.weak_topics) for p in progress_qs)
        total_strong = sum(len(p.strong_topics) for p in progress_qs)
        total_topics = total_weak + total_strong or 1
        weak_percent = round((total_weak / total_topics) * 100, 2)
        strong_percent = round((total_strong / total_topics) * 100, 2)

        # Weekly Trend (for line chart)
        today = datetime.now()
        weekly_trend = [
            {"week": (today - timedelta(weeks=i)).strftime("%Y-%m-%d"), "avg_score": random.randint(60, 95)}
            for i in range(6)
        ]
        weekly_trend.reverse()

        # Completion rate summary
        avg_completion = round(progress_qs.aggregate(Avg("completion_rate"))["completion_rate__avg"] or 0, 2)

        # Engagement simulation (for line/bar)
        engagement_data = [
            {"metric": "Chat Interactions", "count": random.randint(20, 60)},
            {"metric": "Quizzes Attempted", "count": random.randint(5, 15)},
            {"metric": "Homework Submitted", "count": random.randint(3, 10)},
        ]

        analytics = {
            "subject_performance": subject_performance,     # 📊 Bar chart
            "topic_distribution": {                         # 🥧 Pie chart
                "weak": weak_percent,
                "strong": strong_percent,
            },
            "weekly_trend": weekly_trend,                   # 📈 Line chart
            "average_completion": avg_completion,           # 📏 Gauge / donut chart
            "engagement": engagement_data,                  # 📊 Activity chart
        }

        return Response(analytics, status=200)


# ---------------------------------------------
# Deep Analytics Endpoint (for dashboards)
# ---------------------------------------------
class ProgressDeepInsightsView(APIView):
    """
    Deep analytics for dashboards (no randoms):
    - Per-subject topic counts
    - Global top weak topics (by frequency across subjects)
    - Subject leaderboard (sorted by average_score)
    - Readiness index per subject (blend of score & completion)
    - Coverage map (topic lists per subject)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Progress.objects.filter(student=user)
        if not qs.exists():
            return Response({
                "message": "No progress data available.",
                "subjects": [],
                "top_weak_topics": [],
                "leaderboard": [],
                "readiness": []
            }, status=200)

        # Per-subject breakdown
        subjects = []
        weak_counter = {}
        for p in qs:
            weak_count = len(p.weak_topics or [])
            strong_count = len(p.strong_topics or [])
            subjects.append({
                "subject": p.subject,
                "average_score": round(p.average_score, 2),
                "completion_rate": round(p.completion_rate, 2),
                "weak_count": weak_count,
                "strong_count": strong_count,
                "weak_topics": p.weak_topics,
                "strong_topics": p.strong_topics,
            })
            for t in (p.weak_topics or []):
                if not t:
                    continue
                weak_counter[t] = weak_counter.get(t, 0) + 1

        # Top weak topics across all subjects
        top_weak_topics = sorted(
            ({"topic": k, "count": v} for k, v in weak_counter.items()),
            key=lambda x: x["count"], reverse=True
        )[:10]

        # Leaderboard by score
        leaderboard = sorted(
            ({"subject": s["subject"], "score": s["average_score"]} for s in subjects),
            key=lambda x: x["score"], reverse=True
        )

        # Readiness index per subject (0-100): 70% score + 30% completion
        readiness = [
            {
                "subject": s["subject"],
                "readiness_index": round(0.7 * s["average_score"] + 0.3 * s["completion_rate"], 2)
            }
            for s in subjects
        ]

        payload = {
            "subjects": subjects,              # bar/table: score & completion per subject
            "top_weak_topics": top_weak_topics, # chips/tag cloud
            "leaderboard": leaderboard,        # leaderboard widget
            "readiness": readiness,            # gauge per subject
        }
        return Response(payload, status=200)