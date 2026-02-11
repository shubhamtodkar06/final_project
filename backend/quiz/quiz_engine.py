#backend/quiz/quiz_engine.py

from core.ai_manager import ai_generate
from progress.suggestion_engine import suggest_topics


def build_final_topic_list(student, filters, include_suggestions=True):

    user_topics = set(filters.get("topics", []))
    subjects = filters.get("subjects", [])

    if not include_suggestions:
        return list(user_topics), {}

    suggestions = suggest_topics(student, subjects)

    combined = set(user_topics)

    for group in suggestions.values():
        combined.update(group)

    return list(combined), suggestions


def generate_proactive_quiz(student, filters, include_suggestions=True):

    final_topics, suggestions = build_final_topic_list(
        student,
        filters,
        include_suggestions
    )

    if not final_topics:
        final_topics = ["General knowledge"]

    ai_output = ai_generate(
        student_id=student.id,
        query="Generate quiz",
        mode="quiz",
        filters={
            "subjects": filters.get("subjects", []),
            "topics": final_topics
        },
        scope="filtered"
    )

    return ai_output, final_topics, suggestions