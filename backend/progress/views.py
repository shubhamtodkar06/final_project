
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