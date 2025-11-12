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
    Dynamically create prompt depending on use case.
    """
    templates = {
        "chat": f"""You are a friendly tutor for students aged 5–12.
        Answer clearly and educationally.
        Context:\n{context_data}\n
        Student question: {query}
        """,

        "quiz": f"""Generate a short quiz for revision.
        Context:\n{context_data}\n
        Topic: {query}
        Return JSON: {{ "questions": [...], "answers": [...] }}""",

        "homework_feedback": f"""Evaluate the student's homework submission.
        Context:\n{context_data}\n
        Homework Text:\n{query}\n
        Provide JSON: {{ "feedback": "...", "score": float }}""",

        "report": f"""Summarize student's weekly progress.
        Context:\n{context_data}\n
        Create JSON with keys: ['summary', 'improvement_tips']""",

        # ✅ NEW: "note" mode for AI-generated study notes
        "note": f"""You are an educational tutor generating clear, age-appropriate study notes
        for school students (Grades 5–12). Use simple explanations, examples, and subheadings.
        Context:\n{context_data}\n
        User request:\n{query}\n
        Format output as structured markdown or paragraphs.
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