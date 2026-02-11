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
        
class AIWeeklyStudyStrategyView(APIView):
    """
    Proactive + Filter Based Weekly Study Planner

    ✔ Uses student progress
    ✔ Uses topic mastery state
    ✔ Uses RAG through ai_generate
    ✔ Supports user filters
    ✔ Provides AI topic suggestions
    ✔ Multi dimensional planning
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):

        user = request.user

        filters = request.data.get("filters", {}) or {}
        include_suggestions = request.data.get("include_suggestions", True)

        subjects = filters.get("subjects", [])
        user_topics = set(filters.get("topics", []))

        if not subjects:
            return Response(
                {"error": "At least one subject must be provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------------------------
        # Progress Context
        # --------------------------------------------------
        progress_qs = Progress.objects.filter(student=user, subject__in=subjects)

        progress_context = []

        for p in progress_qs:
            progress_context.append({
                "subject": p.subject,
                "average_score": p.average_score,
                "completion_rate": p.completion_rate,
                "weak_topics": p.weak_topics,
                "strong_topics": p.strong_topics
            })

        # --------------------------------------------------
        # Topic Suggestions
        # --------------------------------------------------
        suggestions = {}

        if include_suggestions:
            try:
                from progress.suggestion_engine import suggest_topics

                suggestions = suggest_topics(user, subjects)

                for topic_group in suggestions.values():
                    user_topics.update(topic_group)

            except Exception:
                pass

        # --------------------------------------------------
        # Topic Mastery State
        # --------------------------------------------------
        from progress.models import StudentTopicProgress

        topic_states = []

        for topic_name in user_topics:

            topic_progress = StudentTopicProgress.objects.filter(
                student=user,
                topic__name__iexact=topic_name
            ).first()

            topic_states.append({
                "topic": topic_name,
                "status": topic_progress.status if topic_progress else "available",
                "mastery_score": topic_progress.mastery_score if topic_progress else 0
            })

        # --------------------------------------------------
        # AI Planner Prompt
        # --------------------------------------------------
        planner_prompt = f"""
        Create a structured weekly study strategy.

        Student Progress:
        {progress_context}

        Topic Mastery:
        {topic_states}

        Planning Rules:
        - Focus more time on weak topics
        - Include revision for revision_required topics
        - Reduce effort for mastered topics
        - Create daily breakdown
        - Include homework practice
        - Include quiz practice
        - Suggest revision schedule
        - Keep grade appropriate
        """

        # --------------------------------------------------
        # AI Planner Generation (RAG ENABLED)
        # --------------------------------------------------
        ai_plan = ai_generate(
            student_id=user.id,
            query=planner_prompt,
            mode="planner",
            filters={
                "subjects": subjects,
                "topics": list(user_topics)
            },
            scope="filtered"
        )

        return Response({
            "planner": ai_plan,
            "filters_used": {
                "subjects": subjects,
                "topics": list(user_topics)
            },
            "suggestions": suggestions
        }, status=status.HTTP_200_OK)
        if not progress_qs.exists():
            return Response(
                {"error": "No progress data available to generate study plan."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # -----------------------------
        # Build structured context
        # -----------------------------
        context = ""
        weak_topics = []
        strong_topics = []

        for p in progress_qs:
            context += (
                f"Subject: {p.subject}\n"
                f"Average Score: {p.average_score}\n"
                f"Completion Rate: {p.completion_rate}\n"
                f"Weak Topics: {p.weak_topics}\n"
                f"Strong Topics: {p.strong_topics}\n\n"
            )
            weak_topics.extend(p.weak_topics or [])
            strong_topics.extend(p.strong_topics or [])

        weak_topics = list(set([t for t in weak_topics if t]))
        strong_topics = list(set([t for t in strong_topics if t]))

        # -----------------------------
        # AI Prompt
        # -----------------------------
        prompt = f"""
Create a personalized WEEKLY STUDY STRATEGY for a school student (Grades 5–12).

Student Progress Summary:
{context}

Weak Topics:
{weak_topics}

Strong Topics:
{strong_topics}

STRICT OUTPUT FORMAT (JSON ONLY):

{{
  "subject_wise_plan": {{
    "Subject Name": [
      "Focus topic 1",
      "Focus topic 2"
    ]
  }},
  "daily_plan": {{
    "Monday": "Task description",
    "Tuesday": "Task description",
    "Wednesday": "Task description",
    "Thursday": "Task description",
    "Friday": "Task description",
    "Saturday": "Task description",
    "Sunday": "Light revision / rest"
  }},
  "revision_strategy": [
    "Revision tip 1",
    "Revision tip 2",
    "Revision tip 3"
  ]
}}
"""

        # -----------------------------
        # AI Call
        # -----------------------------
        try:
            ai_response = ai_generate(
                student_id=user.id,
                query=prompt,
                mode="report",
                scope="global"
            )
        except Exception:
            ai_response = "AI strategy generation failed."

        return Response(
            {
                "student": user.username,
                "weak_topics": weak_topics,
                "strong_topics": strong_topics,
                "study_strategy": ai_response,
            },
            status=status.HTTP_200_OK
        )