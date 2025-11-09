#final_project/backend/chatbot/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('resources/add/', views.IngestResourceView.as_view(), name='add_resource'),
]