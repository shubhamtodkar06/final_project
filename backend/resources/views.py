from django.shortcuts import render

# Create your views here.
# backend/resources/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .utils import ingest_resource

class IngestResourceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        title = request.data.get("title")
        content = request.data.get("content", "")
        subject = request.data.get("subject", "")
        grade_level = request.data.get("grade_level", 0)
        file = request.FILES.get("file")

        resource = ingest_resource(
            user=user,
            title=title,
            content=content,
            subject=subject,
            grade_level=grade_level,
            file=file,
            type="student",
        )

        return Response(
            {"message": "Resource ingested and indexed.", "id": resource.id},
            status=status.HTTP_201_CREATED,
        )