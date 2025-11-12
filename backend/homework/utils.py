# backend/homework/utils.py
import re
import json
import logging
from core.ai_manager import ai_generate

logger = logging.getLogger(__name__)

def clean_json_response(raw_text: str):
    """
    Cleans and parses AI JSON safely.
    Handles markdown wrappers, stray characters, or partial JSON.
    """
    if not raw_text:
        return {"feedback": "No response from AI.", "score": 0.0}

    # Remove markdown ```json fences
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()

    # Try direct JSON parsing
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return {
                "feedback": str(data.get("feedback", "No feedback found.")),
                "score": float(data.get("score", 0.0))
            }
    except json.JSONDecodeError:
        logger.warning("⚠️ Primary JSON parse failed, attempting regex extraction.")

    # Try extracting feedback/score manually
    feedback_match = re.search(r'"feedback"\s*:\s*"([^"]+)"', cleaned)
    score_match = re.search(r'"score"\s*:\s*([0-9]+(?:\.[0-9]+)?)', cleaned)

    feedback = feedback_match.group(1) if feedback_match else "AI returned unstructured text."
    score = float(score_match.group(1)) if score_match else 0.0

    return {"feedback": feedback, "score": score}


def evaluate_homework_with_ai(student_id, text, subject):
    """
    Sends homework text to Gemini for evaluation.
    Ensures JSON-structured output, returns dict {feedback, score}.
    """
    logger.info(f"📘 Evaluating homework for student={student_id}, subject={subject}")

    try:
        raw_response = ai_generate(
            student_id=student_id,
            query=f"Evaluate the following {subject} homework:\n{text}\n",
            mode="homework_feedback",
            subject=subject
        )

        logger.debug(f"🧠 Raw AI Output: {raw_response[:500]}")

        result = clean_json_response(raw_response)
        feedback, score = result["feedback"], result["score"]

        # Validate content and ensure sane ranges
        if not feedback or len(feedback.strip()) < 10:
            feedback = "AI feedback incomplete. Please resubmit homework."
        if score < 0 or score > 100:
            score = max(0.0, min(100.0, score))

        return {"feedback": feedback, "score": score}

    except Exception as e:
        logger.error(f"❌ Homework AI evaluation failed: {e}")
        return {"feedback": "AI evaluation failed. Try again later.", "score": 0.0}