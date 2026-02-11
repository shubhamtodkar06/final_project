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
from accounts.models import StudentProfile
from core.filter_resolver import FilterResolver

logger = logging.getLogger(__name__)

# ======================================================
# Embeddings & Vector Store
# ======================================================
embedding_model = HuggingFaceEmbeddings(model_name="all-mpnet-base-v2")

CHROMA_DIR = os.path.join(settings.BASE_DIR, "chroma_store")

vectorstore = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embedding_model
)

# ======================================================
# Gemini LLM
# ======================================================
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# ======================================================
# ⭐ PER STUDENT MEMORY (CRITICAL FIX)
# ======================================================
student_memories = {}


def get_student_memory(student_id):
    if not student_id:
        return ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

    if student_id not in student_memories:
        student_memories[student_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

    return student_memories[student_id]


# ======================================================
# ⭐ FILTER RESOLUTION ENGINE
# ======================================================
def resolve_filters(filters):
    if not filters:
        return None

    try:
        resolver = FilterResolver(filters)
        return resolver.build_metadata_filter()
    except Exception as e:
        logger.warning(f"Filter resolution failed: {e}")
        return None


# ======================================================
# ⭐ RETRIEVER BUILDER
# ======================================================
def build_retriever(filters=None):

    metadata_filter = resolve_filters(filters)

    return vectorstore.as_retriever(
        search_kwargs={
            "k": 4,
            "filter": metadata_filter
        }
    )


# ======================================================
# LEGACY CONTEXT BUILDER
# ======================================================
def fetch_context(student_id=None):
    """
    Adds progress awareness context
    """
    context = ""

    if not student_id:
        return context

    progress_records = Progress.objects.filter(student_id=student_id)

    if not progress_records.exists():
        return context

    scores = []
    weak = set()
    strong = set()

    for p in progress_records:
        if p.average_score is not None:
            scores.append(p.average_score)

        weak.update(p.weak_topics or [])
        strong.update(p.strong_topics or [])

    if scores:
        context += f"Student Average Score: {round(sum(scores)/len(scores),2)}\n"

    if weak:
        context += f"Weak Topics: {', '.join(weak)}\n"

    if strong:
        context += f"Strong Topics: {', '.join(strong)}\n"

    return context


# ======================================================
# ⭐ PROMPT BUILDER
# ======================================================
def build_mode_prompt(mode):

    prompts = {

        "chat":
            "You are an intelligent AI tutor helping student learn concepts clearly.",

        "quiz":
            """Generate MCQ quiz.
Return STRICT JSON:
{
 "questions":[
   {
     "q": "...",
     "options": ["A","B","C","D"],
     "correct": "A"
   }
 ]
}
""",

        "homework_feedback":
            """Evaluate student homework.
Return STRICT JSON:
{
 "feedback":"Detailed explanation",
 "score": number between 0-100
}
""",

        "report":
            "Generate academic progress analysis with suggestions.",

        "study_plan":
            "Create structured weekly study plan using weak topics."

    }

    return prompts.get(mode, "Assist student academically.")


# ======================================================
# ⭐ MAIN AI GENERATOR (CORE ENGINE)
# ======================================================
def ai_generate(
    student_id=None,
    query="",
    mode="chat",
    filters=None,
    scope=None,
    subject=None
):

    try:

        logger.info(
            f"AI run | mode={mode} | scope={scope} | student={student_id}"
        )

        # -----------------------------
        # Memory
        # -----------------------------
        memory = get_student_memory(student_id)

        # -----------------------------
        # Retriever
        # -----------------------------
        retriever = build_retriever(filters)

        # -----------------------------
        # Build Chain
        # -----------------------------
        chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory
        )

        # -----------------------------
        # Build Context
        # -----------------------------
        progress_context = fetch_context(student_id)

        mode_prompt = build_mode_prompt(mode)

        final_prompt = f"""
{mode_prompt}

Student Context:
{progress_context}

User Query:
{query}
"""

        # -----------------------------
        # Execute
        # -----------------------------
        result = chain({"question": final_prompt})

        answer = result.get("answer") or result.get("result")

        return answer

    except Exception as e:
        logger.error(f"AI generation failed [{mode}]: {e}")
        return f"Error: {str(e)}"