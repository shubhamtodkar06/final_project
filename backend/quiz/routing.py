# backend/quiz/routing.py
from django.urls import re_path
from .consumers import QuizConsumer

websocket_urlpatterns = [
    re_path(r"ws/quiz/$", QuizConsumer.as_asgi()),
]