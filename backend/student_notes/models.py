#backend/student_notes/models.py
from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings

class StudentNote(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_notes")
    subject = models.CharField(max_length=100)
    topic = models.CharField(max_length=255)
    ai_note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    source_resources = models.JSONField(default=list, blank=True)  # List of resource IDs or URLs

    def __str__(self):
        return f"{self.student.username} - {self.subject}: {self.topic}"