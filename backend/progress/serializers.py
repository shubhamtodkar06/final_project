#backend/progress/serializer.py
# backend/progress/serializer.py
from rest_framework import serializers
from .models import Progress

class ProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progress
        fields = [
            "id",
            "student",
            "subject",
            "average_score",
            "weak_topics",
            "strong_topics",
            "completion_rate",
            "last_updated",
        ]