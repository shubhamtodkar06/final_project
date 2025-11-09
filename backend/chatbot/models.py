#/Users/set/final_project/backend/chatbot/models.py
from django.db import models
from django.conf import settings

class Resource(models.Model):
    """A resource (document) to be indexed for RAG."""
    title = models.CharField(max_length=255)
    content = models.TextField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="resources")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ChatHistory(models.Model):
    """Stores chat history for a user."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_histories")
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatHistory({self.user}, {self.created_at})"