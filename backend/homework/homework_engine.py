from core.ai_manager import ai_generate
from progress.suggestion_engine import suggest_topics


def build_homework_context(student, filters):

    suggestions = suggest_topics(
        student,
        filters.get("subjects", [])
    )

    topics = filters.get("topics", [])

    for group in suggestions.values():
        topics.extend(group)

    return list(set(topics)), suggestions


def evaluate_proactive_homework(student, filters, text):

    final_topics, suggestions = build_homework_context(student, filters)

    ai_output = ai_generate(
        student_id=student.id,
        query=f"Evaluate this homework:\n{text}",
        mode="homework_feedback",
        filters={
            "subjects": filters.get("subjects", []),
            "topics": final_topics
        },
        scope="filtered"
    )

    return ai_output, final_topics, suggestions