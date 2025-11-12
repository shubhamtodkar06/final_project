from django.urls import path
from .views import GenerateStudentNoteView, ListStudentNotesView

urlpatterns = [
    path("", ListStudentNotesView.as_view(), name="list_student_notes"),
    path("generate/", GenerateStudentNoteView.as_view(), name="generate_student_note"),
]