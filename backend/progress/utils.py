#backend/progress/utils.py

from .models import Progress
from django.utils import timezone

def update_progress_on_quiz(student, subject, correct_topics, wrong_topics):
    """Update progress dynamically after quiz evaluation."""
    progress, _ = Progress.objects.get_or_create(student=student, subject=subject)

    for topic in correct_topics:
        if topic not in progress.strong_topics:
            progress.strong_topics.append(topic)
        if topic in progress.weak_topics:
            progress.weak_topics.remove(topic)

    for topic in wrong_topics:
        if topic not in progress.weak_topics:
            progress.weak_topics.append(topic)

    prev_avg = progress.average_score
    new_avg = (prev_avg + (len(correct_topics) / (len(correct_topics) + len(wrong_topics) + 0.01)) * 100) / 2
    progress.average_score = round(new_avg, 2)
    progress.completion_rate = min(100, progress.completion_rate + 5)
    progress.last_updated = timezone.now()
    progress.save()


# --- New: update_progress_on_homework ---
def update_progress_on_homework(student, subject, score):
    """
    Update the Progress record for the student and subject after homework is graded.
    - Updates average_score as a rolling average with the new homework score.
    - Increases completion_rate by 2%, up to 100%.
    - Updates last_updated.
    """
    progress, _ = Progress.objects.get_or_create(student=student, subject=subject)
    # Rolling average: weighted by number of updates (simulate with completion_rate as proxy)
    # If completion_rate is 0, treat as first score
    prev_avg = progress.average_score
    # Estimate n as completion_rate // 2 (since +2 per homework)
    n = int(progress.completion_rate // 2) if progress.completion_rate else 0
    if n <= 0:
        new_avg = score
    else:
        new_avg = ((prev_avg * n) + score) / (n + 1)
    progress.average_score = round(new_avg, 2)
    progress.completion_rate = min(100, progress.completion_rate + 2)
    progress.last_updated = timezone.now()
    progress.save()