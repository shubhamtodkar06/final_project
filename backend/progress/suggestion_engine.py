#backend/progress/suggestion_engine.py

from .models import StudentTopicProgress


def suggest_topics(student, subjects=None):
    """
    Suggest topics using proactive analytics.
    """

    qs = StudentTopicProgress.objects.filter(student=student)

    if subjects:
        qs = qs.filter(topic__subject__name__in=subjects)

    suggestions = {
        "revision": [],
        "weak": [],
        "in_progress": [],
        "next_topics": []
    }

    for record in qs.select_related("topic", "topic__subject"):

        topic_name = record.topic.name

        if record.status == "revision_required":
            suggestions["revision"].append(topic_name)

        elif record.status == "in_progress":
            suggestions["in_progress"].append(topic_name)

        elif record.status == "available":
            suggestions["next_topics"].append(topic_name)

    # Low mastery → weak topics
    suggestions["weak"] = [
        r.topic.name
        for r in qs
        if r.mastery_score < 50 and r.status != "locked"
    ]

    return suggestions