# backend/progress/utils.py

from django.utils import timezone
from .models import Progress
from .topic_engine import update_topic_mastery
from student_notes.models import Topic


# ======================================================
# QUIZ PROGRESS UPDATE
# ======================================================

def update_progress_on_quiz(student, subject, correct_topics, wrong_topics):   
    """
    Update subject-level progress + topic mastery after quiz.
    """

    progress, _ = Progress.objects.get_or_create(
        student=student,
        subject=subject
    )

    # -------------------------
    # Update Strong / Weak topics
    # -------------------------
    for topic in correct_topics:
        if topic not in progress.strong_topics:
            progress.strong_topics.append(topic)

        if topic in progress.weak_topics:
            progress.weak_topics.remove(topic)

    for topic in wrong_topics:
        if topic not in progress.weak_topics:
            progress.weak_topics.append(topic)

    # -------------------------
    # Update Subject Score
    # -------------------------
    total = len(correct_topics) + len(wrong_topics)
    quiz_score = (len(correct_topics) / total) * 100 if total else 0

    prev_avg = progress.average_score
    new_avg = (prev_avg + quiz_score) / 2
    progress.average_score = round(new_avg, 2)

    progress.completion_rate = min(100, progress.completion_rate + 5)
    progress.last_updated = timezone.now()
    progress.save()

    # -------------------------
    # NEW ⭐ Update Topic Mastery
    # -------------------------
    for topic_name in correct_topics:
        topic_obj = Topic.objects.filter(
            name__iexact=topic_name,
            subject__name__iexact=subject
        ).first()

        if topic_obj:
            update_topic_mastery(student, topic_obj, 90)

    for topic_name in wrong_topics:
        topic_obj = Topic.objects.filter(
            name__iexact=topic_name,
            subject__name__iexact=subject
        ).first()

        if topic_obj:
            update_topic_mastery(student, topic_obj, 40)


# ======================================================
# HOMEWORK PROGRESS UPDATE
# ======================================================

def update_progress_on_homework(student, subject, score, topic_name=None):
    """
    Update subject progress + topic mastery using homework score.
    """

    progress, _ = Progress.objects.get_or_create(
        student=student,
        subject=subject
    )

    # -------------------------
    # Rolling Average
    # -------------------------
    prev_avg = progress.average_score

    if progress.completion_rate == 0:
        new_avg = score
    else:
        new_avg = (prev_avg + score) / 2

    progress.average_score = round(new_avg, 2)
    progress.completion_rate = min(100, progress.completion_rate + 2)
    progress.last_updated = timezone.now()
    progress.save()

    # -------------------------
    # NEW ⭐ Topic Mastery Update
    # -------------------------
    if topic_name:
        topic_obj = Topic.objects.filter(
            name__iexact=topic_name,
            subject__name__iexact=subject
        ).first()

        if topic_obj:
            update_topic_mastery(student, topic_obj, score)