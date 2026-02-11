#backend/progress/topic_engine.py

from django.utils import timezone
from student_notes.models import Topic
from .models import StudentTopicProgress


MASTERY_THRESHOLD = 75


def update_topic_mastery(student, topic, score):

    progress, _ = StudentTopicProgress.objects.get_or_create(
        student=student,
        topic=topic
    )

    progress.mastery_score = (progress.mastery_score + score) / 2
    progress.last_attempt = timezone.now()

    if progress.mastery_score >= MASTERY_THRESHOLD:
        progress.status = "mastered"
        unlock_next_topic(student, topic)
    else:
        progress.status = "in_progress"

    progress.save()


def unlock_next_topic(student, topic):

    next_topic = Topic.objects.filter(
        subject=topic.subject,
        order_index__gt=topic.order_index
    ).order_by("order_index").first()

    if not next_topic:
        return

    StudentTopicProgress.objects.get_or_create(
        student=student,
        topic=next_topic,
        defaults={"status": "available"}
    )