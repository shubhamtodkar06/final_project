#backend/quiz/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("generate/", views.generate_quiz, name="generate_quiz"),
    path("<int:quiz_id>/submit/", views.submit_quiz, name="submit_quiz"),
]