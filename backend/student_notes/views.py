# backend/student_notes/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from accounts.models import StudentProfile
from progress.models import Progress, StudentTopicProgress
from progress.suggestion_engine import suggest_topics
from resources.models import Resource
from core.ai_manager import ai_generate

from .models import Standard, Subject, Topic, MasterNote, AINote


# ==========================================================
# ⭐ PROACTIVE + FILTER BASED NOTE GENERATOR
# ==========================================================

class GenerateStudentNoteView(APIView):
    """
    Proactive + Filter-based AI Note Generator

    ✔ Multi-subject / multi-topic filters
    ✔ Uses progress analytics
    ✔ Uses topic mastery
    ✔ Uses RAG via ai_manager
    ✔ Suggests topics automatically
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
                {"error": "At least one subject must be provided in filters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------------------------
        # PROFILE + STANDARD
        # --------------------------------------------------
        profile = StudentProfile.objects.get(user=user)
        standard = Standard.objects.get(grade=profile.grade)

        # --------------------------------------------------
        # ⭐ PROACTIVE TOPIC SUGGESTIONS
        # --------------------------------------------------
        suggestions = {}

        if include_suggestions:
            try:
                suggestions = suggest_topics(user, subjects)

                for topic_group in suggestions.values():
                    user_topics.update(topic_group)

            except Exception:
                pass

        final_topics = list(user_topics)

        # --------------------------------------------------
        # RESOLVE SUBJECT + TOPIC OBJECTS
        # --------------------------------------------------
        resolved_topics = []

        for subject_name in subjects:

            subject_obj = Subject.objects.filter(
                name__iexact=subject_name,
                standard=standard
            ).first()

            if not subject_obj:
                continue

            for topic_name in final_topics:

                topic_obj = Topic.objects.filter(
                    name__iexact=topic_name,
                    subject=subject_obj
                ).first()

                if topic_obj:
                    resolved_topics.append(topic_obj)

        if not resolved_topics:
            return Response(
                {"error": "No valid topics found from filters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------------------------
        # ⭐ LEARNING STATE DETECTION
        # --------------------------------------------------
        topic_states = []

        for topic in resolved_topics:

            progress = StudentTopicProgress.objects.filter(
                student=user,
                topic=topic
            ).first()

            state = progress.status if progress else "available"

            topic_states.append({
                "subject": topic.subject.name,
                "topic": topic.name,
                "state": state
            })

        # --------------------------------------------------
        # ⭐ RESOURCE CONTEXT (RAG)
        # --------------------------------------------------
        resource_context = ""

        try:
            resource_qs = Resource.objects.filter(
                subject__in=subjects,
                grade_level=profile.grade
            )[:5]

            resource_context = "\n".join([
                f"{r.title}: {(r.content or r.extracted_text or '')[:200]}"
                for r in resource_qs
            ])

        except Exception:
            pass

        # --------------------------------------------------
        # ⭐ BUILD AI PROMPT
        # --------------------------------------------------
        learning_context = "\n".join([
            f"{t['subject']} → {t['topic']} ({t['state']})"
            for t in topic_states
        ])

        prompt = f"""
        Generate structured study notes.

        Learning Targets:
        {learning_context}

        Reference Materials:
        {resource_context}

        Rules:
        - If topic is 'available' → beginner explanation
        - If 'in_progress' → detailed conceptual notes + examples
        - If 'revision_required' → summarized revision notes
        - If 'mastered' → advanced reinforcement notes
        - Keep grade appropriate
        """

        # --------------------------------------------------
        # ⭐ AI + RAG GENERATION
        # --------------------------------------------------
        ai_content = ai_generate(
            student_id=user.id,
            query=prompt,
            mode="note",
            filters={
                "subjects": subjects,
                "topics": [t.name for t in resolved_topics]
            },
            scope="filtered"
        )

        # --------------------------------------------------
        # ⭐ SAVE NOTES
        # --------------------------------------------------
        saved_notes = []

        for topic in resolved_topics:

            note = AINote.objects.create(
                student=user,
                standard=standard,
                subject=topic.subject,
                topic=topic,
                content=ai_content,
                generated_reason="proactive_filter_based"
            )

            saved_notes.append({
                "subject": topic.subject.name,
                "topic": topic.name,
                "created_at": note.created_at
            })

        return Response({
            "message": "Proactive AI notes generated successfully",
            "topics_used": [t.name for t in resolved_topics],
            "suggestions": suggestions,
            "notes_created": saved_notes,
            "content": ai_content
        }, status=status.HTTP_201_CREATED)


# ==========================================================
# READ NOTES
# ==========================================================

class NotesGlobalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = StudentProfile.objects.get(user=user)

        admin_notes = MasterNote.objects.filter(standard__grade=profile.grade)
        ai_notes = AINote.objects.filter(student=user)

        return Response({
            "admin_notes": [
                {
                    "subject": n.subject.name,
                    "topic": n.topic.name,
                    "content": n.content
                } for n in admin_notes
            ],
            "ai_notes": [
                {
                    "subject": n.subject.name,
                    "topic": n.topic.name if n.topic else None,
                    "content": n.content
                } for n in ai_notes
            ]
        })


class NotesSubjectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, subject):
        user = request.user
        profile = StudentProfile.objects.get(user=user)
        standard = Standard.objects.get(grade=profile.grade)
        subject_obj = Subject.objects.get(name__iexact=subject, standard=standard)

        admin_notes = MasterNote.objects.filter(subject=subject_obj)
        ai_notes = AINote.objects.filter(student=user, subject=subject_obj)

        return Response({
            "subject": subject_obj.name,
            "admin_notes": [
                {"topic": n.topic.name, "content": n.content}
                for n in admin_notes
            ],
            "ai_notes": [
                {"topic": n.topic.name if n.topic else None, "content": n.content}
                for n in ai_notes
            ]
        })


class NotesTopicView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, subject, topic):
        user = request.user
        profile = StudentProfile.objects.get(user=user)
        standard = Standard.objects.get(grade=profile.grade)
        subject_obj = Subject.objects.get(name__iexact=subject, standard=standard)
        topic_obj = Topic.objects.get(name__iexact=topic, subject=subject_obj)

        admin_notes = MasterNote.objects.filter(subject=subject_obj, topic=topic_obj)
        ai_notes = AINote.objects.filter(student=user, subject=subject_obj, topic=topic_obj)

        return Response({
            "subject": subject_obj.name,
            "topic": topic_obj.name,
            "admin_notes": [{"content": n.content} for n in admin_notes],
            "ai_notes": [{"content": n.content} for n in ai_notes]
        })