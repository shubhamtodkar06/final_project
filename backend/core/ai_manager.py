# backend/core/ai_manager.py
import os
import logging
from django.conf import settings
from langchain.chains import ConversationalRetrievalChain
from langchain.vectorstores import Chroma
from langchain.memory import ConversationBufferMemory
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from progress.models import Progress
from resources.models import Resource

logger = logging.getLogger(__name__)

# === Embeddings & Vector Store (shared globally) ===
embedding_model = HuggingFaceEmbeddings(model_name="all-mpnet-base-v2")
CHROMA_DIR = os.path.join(settings.BASE_DIR, "chroma_store")
vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embedding_model)

# === Gemini LLM (shared globally) ===
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# === Universal memory (for chat) ===
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# === Create base RAG pipeline ===
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    memory=memory
)


def fetch_context(student_id=None, subject=None):
    """
    Fetch relevant info from ChromaDB and progress data.
    Enrich context with student's overall average score and combined weak/strong topics.
    This context is used for all query types (chat, quiz, homework, report).
    """
    context_data = ""

    overall_avg = None
    overall_weak = set()
    overall_strong = set()
    progress_records = []
    if student_id:
        progress_records = list(Progress.objects.filter(student_id=student_id))
        # Compute overall average score
        scores = [p.average_score for p in progress_records if p.average_score is not None]
        if scores:
            overall_avg = round(sum(scores) / len(scores), 2)
        # Gather all weak/strong topics across all subjects
        for p in progress_records:
            overall_weak.update([t for t in (p.weak_topics or []) if t])
            overall_strong.update([t for t in (p.strong_topics or []) if t])

    # Add overall stats to context if available
    if overall_avg is not None:
        context_data += f"Student Average Score: {overall_avg}\n"
    if overall_weak:
        context_data += f"Overall Weak Topics: {', '.join(sorted(overall_weak))}\n"
    if overall_strong:
        context_data += f"Overall Strong Topics: {', '.join(sorted(overall_strong))}\n"

    # Add per-subject breakdown
    for p in progress_records:
        context_data += (
            f"\nSubject: {p.subject}\n"
            f"Weak Topics: {p.weak_topics}\n"
            f"Strong Topics: {p.strong_topics}\n"
        )

    # Subject-based notes (resources)
    if subject:
        resources = Resource.objects.filter(subject__icontains=subject)[:5]
        for r in resources:
            context_data += f"\nTitle: {r.title}\n{r.content[:300]}...\n"

    return context_data.strip()


def build_prompt(mode, query, context_data=""):
    """
    Dynamically create prompt depending on use case with improved clarity and explicit structure.
    """
    templates = {
        "chat": f"""ROLE: You are a kind, supportive AI tutor for students aged 5–12. 
        TASK: Respond to the student's question with simple, educational, and encouraging explanations.
        TONE: Friendly, patient, and age-appropriate.
        CONTEXT:\n{context_data}\n
        QUESTION:\n{query}\n
        OUTPUT INSTRUCTIONS:
        - Write short and clear answers (2–4 sentences).
        - Include one simple example if possible.
        - Avoid technical jargon, use real-life analogies.
        """,

        "quiz": f"""ROLE: You are a quiz generator for school students (Grades 5–12).
        TASK: Create multiple-choice questions based on the provided topic.
        CONTEXT (student progress and available resources):\n{context_data}\n
        TOPIC: {query}
        STRICT OUTPUT REQUIREMENTS:
        1. You must return ONLY valid JSON (no markdown, no code blocks, no explanations).
        2. The JSON object must have one key: "questions".
        3. Each item in "questions" must include:
           - "q": the question text (string)
           - "options": a list of 4 short answer choices (strings)
           - "correct": exactly one correct answer from the list (string)
        4. Questions should be short, factual, and suitable for ages 5–12.
        5. Return 4–6 questions.
        EXAMPLE OUTPUT:
        {{
            "questions": [
                {{
                    "q": "What does a fraction represent?",
                    "options": ["A whole number", "A part of a whole", "A decimal", "A shape"],
                    "correct": "A part of a whole"
                }},
                {{
                    "q": "In the fraction 3/4, what is the numerator?",
                    "options": ["3", "4", "7", "1"],
                    "correct": "3"
                }}
            ]
        }}
        """,

        "homework_feedback": f"""ROLE: You are a teacher evaluating a student's homework.
        TASK: Provide concise, helpful feedback and assign a score between 0 and 100.
        CONTEXT:\n{context_data}\n
        HOMEWORK SUBMISSION:\n{query}\n
        STRICT OUTPUT REQUIREMENTS:
        1. Return ONLY valid JSON (no markdown, no code fences, no explanations).
        2. The JSON object must have these keys:
           - "feedback": a short paragraph (2–4 sentences) describing what was good and what needs improvement.
           - "score": a float number between 0.0 and 100.0.
        EXAMPLE OUTPUT:
        {{
            "feedback": "Good effort! You understood fractions but made a few mistakes with denominators. Revise that section.",
            "score": 78.5
        }}
        """,

        "report": f"""ROLE: You are an AI progress analyst summarizing a student's weekly learning performance.
        TASK: Generate a parent-friendly summary and improvement tips.
        CONTEXT:\n{context_data}\n
        DATA SUMMARY INPUT:\n{query}\n
        STRICT OUTPUT FORMAT:
        {{
            "summary": "Short 2–3 sentence summary of student performance.",
            "improvement_tips": ["Tip 1", "Tip 2", "Tip 3"]
        }}
        """,

        "note": f"""ROLE: You are an AI educational content generator creating personalized study notes.
        TASK: Generate age-appropriate, easy-to-understand notes for Grades 5–12 students.
        CONTEXT:\n{context_data}\n
        USER REQUEST:\n{query}\n
        OUTPUT INSTRUCTIONS:
        - Provide content in markdown-like structured text (with **headings** and bullet points).
        - Include definitions, examples, and a short summary section.
        - Avoid excessive details, keep the tone simple and engaging.
        EXAMPLE OUTPUT:
        ## Fractions Explained
        - A fraction shows parts of a whole.
        - Example: 1/2 means one out of two equal parts.
        **Tip:** Practice by dividing shapes into equal parts.
        """
    }
    return templates.get(mode, query)

def ai_generate(student_id, query, mode="chat", subject=None):
    """
    🔹 Universal AI entrypoint
    - Fetch context
    - Build mode-specific prompt
    - Call Gemini through LangChain RAG
    """
    try:
        context_data = fetch_context(student_id=student_id, subject=subject)
        final_prompt = build_prompt(mode, query, context_data)

        logger.info(f"Running AI ({mode}) for student={student_id}, subject={subject}")
        result = qa_chain.run(final_prompt)
        return result
    except Exception as e:
        logger.error(f"AI generation failed [{mode}]: {e}")
        return f"Error: {str(e)}"