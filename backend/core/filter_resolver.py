# backend/core/filter_resolver.py

from accounts.models import StudentProfile
from progress.models import Progress, StudentTopicProgress
from student_notes.models import Topic


class FilterResolver:

    @staticmethod
    def resolve(student, manual_filters=None):

        # -----------------------------
        # 1️⃣ Manual Filters Override
        # -----------------------------
        if manual_filters:
            if manual_filters.get("subjects") or manual_filters.get("topics"):
                return {
                    "subjects": manual_filters.get("subjects", []),
                    "topics": manual_filters.get("topics", []),
                    "priority_reason": "manual_selection"
                }

        # -----------------------------
        # 2️⃣ Get Student Profile
        # -----------------------------
        profile = StudentProfile.objects.filter(user=student).first()
        grade = profile.grade if profile else None

        # -----------------------------
        # 3️⃣ Revision Due Topics
        # -----------------------------
        revision_topics = StudentTopicProgress.objects.filter(
            student=student,
            status="revision_required"
        ).values_list("topic__name", flat=True)

        if revision_topics:
            return {
                "subjects": [],
                "topics": list(revision_topics),
                "priority_reason": "revision_due"
            }

        # -----------------------------
        # 4️⃣ Weak Topics
        # -----------------------------
        weak_topics = []
        progress_qs = Progress.objects.filter(student=student)

        for p in progress_qs:
            weak_topics.extend(p.weak_topics)

        if weak_topics:
            return {
                "subjects": [],
                "topics": list(set(weak_topics)),
                "priority_reason": "weak_topics"
            }

        # -----------------------------
        # 5️⃣ Current Learning Topics
        # -----------------------------
        active_topics = StudentTopicProgress.objects.filter(
            student=student,
            status__in=["available", "in_progress"]
        ).values_list("topic__name", flat=True)

        if active_topics:
            return {
                "subjects": [],
                "topics": list(active_topics),
                "priority_reason": "current_learning"
            }

        # -----------------------------
        # 6️⃣ Fallback
        # -----------------------------
        return {
            "subjects": [],
            "topics": [],
            "priority_reason": "fallback"
        }