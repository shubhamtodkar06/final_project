#backend/chatbot/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Resource
from .utils import index_resource

class IngestResourceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        title = request.data.get("title")
        content = request.data.get("content")
        if not title or not content:
            return Response({"error": "title and content required"}, status=status.HTTP_400_BAD_REQUEST)
        resource = Resource.objects.create(
            title=title,
            content=content,
            owner=request.user
        )
        index_resource(resource)
        return Response({"message": "Resource ingested and indexed."}, status=status.HTTP_201_CREATED)
