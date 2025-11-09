# backend/myproject/asgi.py
import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# ✅ Set default settings module for Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# ✅ Explicitly initialize Django before importing any app modules
django.setup()

# ✅ Import routing after Django setup to avoid ImproperlyConfigured errors
import chatbot.routing

# ✅ Define ASGI application for HTTP + WebSocket
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chatbot.routing.websocket_urlpatterns
        )
    ),
})