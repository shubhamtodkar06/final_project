# backend/chatbot/utils.py

# backend/chatbot/utils.py

# All model orchestration is now handled by core.ai_manager.
from core.ai_manager import ai_generate

def generate_stream_with_context(student_id, query, user=None, session_id=None):
    """
    Backward-compatible wrapper for AI response generation.
    Uses centralized ai_generate().
    """
    try:
        answer = ai_generate(student_id, query, mode="chat")
        return [answer], answer
    except Exception as e:
        return [f"Error: {str(e)}"], f"Error: {str(e)}"