#backend/recommendations/models.py
from django.db import models
from django.conf import settings

# Create your models here.
class Recommendation(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField()
    resource_link = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)