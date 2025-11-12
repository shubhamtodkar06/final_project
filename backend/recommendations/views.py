#backend/recommendations/views.py
# backend/recommendations/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from progress.models import Progress
from resources.models import Resource
from core.ai_manager import ai_generate

class AIRecommendationsView(APIView):
    """
    Analyze student's weak topics and recommend relevant resources using AI.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Fetch all progress records for the current user
        progress_qs = Progress.objects.filter(student=user)
        weak_topics = []
        for p in progress_qs:
            weak_topics.extend(p.weak_topics)
        weak_topics = list(set([t for t in weak_topics if t]))
        if not weak_topics:
            return Response(
                {"message": "No weak topics found for recommendations.", "recommendations": [], "resources": []},
                status=status.HTTP_200_OK,
            )

        # Use AI to generate personalized study recommendations
        topics_str = ", ".join(weak_topics)
        ai_suggestion = ai_generate(user.id, f"Suggest study tips and resources for these topics: {topics_str}", mode="report")

        # Find top 3 related resources (by topic match in title/content/subject)
        resource_qs = Resource.objects.filter(
            type__in=["system", "ai"]
        ).filter(
            # very simple matching: any topic in title/content/subject
        )
        # Build a scoring system: count number of weak topics matched
        def resource_score(resource):
            text = f"{resource.title} {resource.content} {resource.subject}".lower()
            return sum(1 for t in weak_topics if t.lower() in text)
        resources = sorted(resource_qs, key=resource_score, reverse=True)
        top_resources = []
        for r in resources:
            if resource_score(r) > 0:
                top_resources.append({
                    "id": r.id,
                    "title": r.title,
                    "subject": r.subject,
                    "grade_level": r.grade_level,
                    "uploaded_at": r.uploaded_at,
                })
            if len(top_resources) >= 3:
                break

        return Response(
            {
                "message": "Personalized recommendations generated.",
                "weak_topics": weak_topics,
                "ai_suggestion": ai_suggestion,
                "resources": top_resources,
            },
            status=status.HTTP_200_OK,
        )