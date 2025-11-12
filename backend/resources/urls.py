# backend/resources/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("add/", views.IngestResourceView.as_view(), name="add_resource"),
]