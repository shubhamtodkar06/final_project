# backend/homework/routing.py
from django.urls import re_path
from .consumers import HomeworkConsumer

websocket_urlpatterns = [
    re_path(r"ws/homework/$", HomeworkConsumer.as_asgi()),
]