#backend/student_notes/models.py
from django.db import models
from django.conf import settings

class Standard(models.Model):
    grade = models.IntegerField(unique=True)

    def __str__(self):
        return f"Grade {self.grade}"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("name", "standard")

    def __str__(self):
        return f"{self.name} (Grade {self.standard.grade})"


class Topic(models.Model):
    name = models.CharField(max_length=150)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    order_index = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} - {self.subject}"


class MasterNote(models.Model):
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    content = models.TextField()
    source = models.CharField(
        max_length=20,
        choices=[("admin", "Admin"), ("teacher", "Teacher")],
        default="admin"
    )
    created_at = models.DateTimeField(auto_now_add=True)


class AINote(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    standard = models.ForeignKey(Standard, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, blank=True)

    content = models.TextField()
    generated_reason = models.CharField(
        max_length=100,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)