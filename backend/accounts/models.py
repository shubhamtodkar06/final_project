#backend/accounts/models.py
from django.db import models
from django.conf import settings
# Create your models here.
# accounts/models.py

class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    grade = models.IntegerField()   # 5–12
    board = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} (Grade {self.grade})"