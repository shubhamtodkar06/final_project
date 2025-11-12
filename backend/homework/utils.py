#backend/homework/utils.py
import json
from core.ai_manager import ai_generate

def evaluate_homework_with_ai(student_id, text, subject):
    """
    Calls ai_generate with mode="homework_feedback", parses response JSON, returns feedback and score.
    """
    result = ai_generate(student_id, text, mode="homework_feedback", subject=subject)
    try:
        data = json.loads(result)
        feedback = data.get("feedback", "")
        score = data.get("score", 0)
        return {"feedback": feedback, "score": score}
    except Exception:
        # fallback if not JSON
        return {"feedback": result, "score": 0}

