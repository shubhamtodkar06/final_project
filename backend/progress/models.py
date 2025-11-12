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