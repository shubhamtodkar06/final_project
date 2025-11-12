from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import StudentNote
from .serializers import StudentNoteSerializer
from core.ai_manager import ai_generate
from progress.models import Progress
from resources.models import Resource

class GenerateStudentNoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        student = request.user
        subject = request.data.get("subject")
        topic = request.data.get("topic")
        prompt = request.data.get("prompt", "Generate detailed study notes for this topic")

        if not subject or not topic:
            return Response({"error": "Subject and topic are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Gather progress context
        progress_data = Progress.objects.filter(student=student, subject__iexact=subject).first()
        weak_topics = progress_data.weak_topics if progress_data else []
        strong_topics = progress_data.strong_topics if progress_data else []

        # Gather related resources
        related_resources = Resource.objects.filter(subject__icontains=subject)[:5]
        resource_context = "\n".join([f"{r.title}: {r.content[:250]}" for r in related_resources])

        # Build contextual query
        query = f"""
        Create detailed study notes for topic: {topic} (Subject: {subject}).
        Consider student progress:
        Weak topics: {weak_topics}, Strong topics: {strong_topics}.
        Additional resources:
        {resource_context}
        """

        # Generate AI-based notes
        ai_response = ai_generate(student.id, query, mode="note", subject=subject)

        # Save note
        note = StudentNote.objects.create(
            student=student,
            subject=subject,
            topic=topic,
            ai_note=ai_response,
            source_resources=[r.id for r in related_resources]
        )

        return Response(
            {
                "message": "AI study note generated successfully.",
                "note": StudentNoteSerializer(note).data
            },
            status=status.HTTP_201_CREATED
        )


class ListStudentNotesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notes = StudentNote.objects.filter(student=request.user).order_by("-created_at")
        return Response(StudentNoteSerializer(notes, many=True).data)