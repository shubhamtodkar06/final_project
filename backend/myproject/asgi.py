# backend/myproject/asgi.py
import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

# Import app websocket routes after setup
import chatbot.routing
try:
    import homework.routing
except Exception:
    homework = None
try:
    import quiz.routing
except Exception:
    quiz = None

# Aggregate websocket patterns
ws_patterns = []
ws_patterns += getattr(chatbot.routing, 'websocket_urlpatterns', [])
if homework:
    ws_patterns += getattr(homework.routing, 'websocket_urlpatterns', [])
if quiz:
    ws_patterns += getattr(quiz.routing, 'websocket_urlpatterns', [])

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(ws_patterns)
    ),
})