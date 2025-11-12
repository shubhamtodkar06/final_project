# backend/myproject/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

# Health check endpoint for Render / local debugging
def health_check(request):
    return JsonResponse({"status": "ok", "message": "Server is running"})

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path('api/auth/', include('accounts.urls')),

    # Chatbot + RAG
    path('api/chatbot/', include('chatbot.urls')),

    # Resource management
    path('api/resources/', include('resources.urls')),

    # Homework upload + feedback
    path('api/homework/', include('homework.urls')),

    # Quiz generation + submission
    path('api/quiz/', include('quiz.urls')),

    # Student progress tracking
    path('api/progress/', include('progress.urls')),

    # Personalized recommendations
    path('api/recommendations/', include('recommendations.urls')),

    # Parent / Weekly reports
    path('api/reports/', include('reports.urls')),

    # Health check (for Render)
    path('healthz/', health_check),
]