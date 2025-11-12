#backend/reports/models.py
from django.db import models
from django.conf import settings

# Create your models here.
class Report(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    week_range = models.CharField(max_length=100)
    summary = models.TextField()
    progress_data = models.JSONField()
    sent_at = models.DateTimeField(auto_now_add=True)