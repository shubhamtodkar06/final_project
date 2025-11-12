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
    """
    context_data = ""

    # Student progress (personalized insight)
    if student_id:
        progress_records = Progress.objects.filter(student_id=student_id)
        for p in progress_records:
            context_data += f"\nSubject: {p.subject}\nWeak Topics: {p.weak_topics}\nStrong Topics: {p.strong_topics}\n"

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
        Create JSON with keys: ['summary', 'improvement_tips']"""
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