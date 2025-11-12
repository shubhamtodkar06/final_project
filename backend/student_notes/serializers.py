from rest_framework import serializers
from .models import StudentNote

class StudentNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentNote
        fields = ["id", "subject", "topic", "ai_note", "created_at", "source_resources"]