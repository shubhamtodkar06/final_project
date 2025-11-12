#final_project/backend/chatbot/urls.py
from django.urls import path
from . import views

urlpatterns = [

    # Session management
    path('sessions/', views.ChatSessionListCreateView.as_view(), name='chat_sessions'),
    path('sessions/<uuid:session_id>/', views.ChatSessionRetrieveDeleteView.as_view(), name='chat_session_detail'),
    path('sessions/<uuid:session_id>/messages/', views.ChatMessageListView.as_view(), name='chat_session_messages'),
]