#backend/progress/models.py
from django.db import models
from django.conf import settings

# Create your models here.
class Progress(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    average_score = models.FloatField(default=0)
    weak_topics = models.JSONField(default=list)
    strong_topics = models.JSONField(default=list)
    completion_rate = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
class StudentTopicProgress(models.Model):
    """
    Tracks per-topic learning state for proactive tutoring.
    Controls topic unlocking, mastery scoring, and revision scheduling.
    """

    STATUS_CHOICES = [
        ("locked", "Locked"),
        ("available", "Available"),
        ("in_progress", "In Progress"),
        ("mastered", "Mastered"),
        ("revision_required", "Revision Required"),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    topic = models.ForeignKey("student_notes.Topic", on_delete=models.CASCADE)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="locked")
    mastery_score = models.FloatField(default=0)

    last_attempt = models.DateTimeField(blank=True, null=True)
    revision_due = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("student", "topic")

    def __str__(self):
        return f"{self.student} - {self.topic} ({self.status})"