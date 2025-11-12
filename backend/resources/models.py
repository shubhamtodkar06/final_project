#backend/resources/models.py
from django.db import models
from django.conf import settings

# Create your models here.
class Resource(models.Model):
    TYPE_CHOICES = [
        ("system", "System"),
        ("ai", "AI"),
        ("student", "Student"),
    ]
    title = models.CharField(max_length=255)
    content = models.TextField()
    subject = models.CharField(max_length=100)
    grade_level = models.IntegerField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='resources/files/', blank=True, null=True)
    type = models.CharField(max_length=16, choices=TYPE_CHOICES, default="system")
    extracted_text = models.TextField(blank=True, null=True)
    source_link = models.URLField(blank=True, null=True)
    embedding_vector = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} ({self.subject})"