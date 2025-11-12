#backend/quiz/models.py
from django.db import models
from django.conf import settings

# Create your models here.
class Quiz(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    questions = models.JSONField()
    student_answers = models.JSONField(null=True, blank=True)
    ai_feedback = models.TextField(null=True, blank=True)
    score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)