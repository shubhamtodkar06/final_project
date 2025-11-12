# backend/chatbot/serializers.py
# backend/chatbot/serializers.py
from rest_framework import serializers
from .models import ChatSession, ChatMessage

class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ["id", "title", "created_at"]

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "sender", "content", "created_at"]