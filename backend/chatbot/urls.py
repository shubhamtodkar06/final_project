# backend/chatbot/urls.py
from django.urls import path
from .views import (
    ChatSessionListCreateView,
    ChatSessionRetrieveDeleteView,
    ChatMessageListView,
    ChatbotAPIView
)

urlpatterns = [
    # Session management
    path('sessions/', ChatSessionListCreateView.as_view(), name='chat_sessions'),
    path('sessions/<uuid:session_id>/', ChatSessionRetrieveDeleteView.as_view(), name='chat_session_detail'),
    path('sessions/<uuid:session_id>/messages/', ChatMessageListView.as_view(), name='chat_session_messages'),

    # Chat interaction
    path('chat/', ChatbotAPIView.as_view(), name='chat'),
]