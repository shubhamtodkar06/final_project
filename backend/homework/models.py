#backend/homework/models.py
from django.db import models
from django.conf import settings

# Create your models here.
class Homework(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    text_content = models.TextField()
    ai_feedback = models.TextField(blank=True, null=True)
    score = models.FloatField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)