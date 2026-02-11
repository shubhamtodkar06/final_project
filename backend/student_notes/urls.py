from django.urls import path
from .views import (
    NotesGlobalView,
    NotesSubjectView,
    NotesTopicView,
    GenerateStudentNoteView,
)

urlpatterns = [
    # AI note generation
    path("generate/", GenerateStudentNoteView.as_view(), name="notes-generate"),

    # Read notes
    path("global/", NotesGlobalView.as_view(), name="notes-global"),
    path("subject/<str:subject>/", NotesSubjectView.as_view(), name="notes-subject"),
    path("topic/<str:subject>/<str:topic>/", NotesTopicView.as_view(), name="notes-topic"),
]