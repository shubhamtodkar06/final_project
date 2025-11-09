# backend/chatbot/utils.py
import os
from django.conf import settings
from django.utils import timezone
from .vector_store import get_student_collection, get_global_collection
from sentence_transformers import SentenceTransformer
from google import genai

# Initialize Gemini client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
TEXT_MODEL = "gemini-2.5-flash"

_embedding_model = SentenceTransformer('all-mpnet-base-v2')


def get_embedding(text: str):
    """Generate embedding using local SentenceTransformer model."""
    text = (text or "").strip()
    if not text:
        return [0.0] * 768
    return _embedding_model.encode(text).tolist()


def index_resource(resource):
    """Index a resource into the vector store."""
    content = resource.content or ""
    if not content.strip():
        return

    chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]
    embeddings = [get_embedding(chunk) for chunk in chunks]
    ids = [f"resource_{resource.id}_chunk{i}" for i in range(len(chunks))]

    global_collection = get_global_collection()
    global_collection.add(documents=chunks, embeddings=embeddings, ids=ids)

    if resource.owner_id:
        student_collection = get_student_collection(str(resource.owner_id))
        student_collection.add(documents=chunks, embeddings=embeddings, ids=ids)


def retrieve_context(student_id: str, query: str, top_k: int = 3) -> str:
    """Retrieve relevant context from student + global data."""
    query_embedding = get_embedding(query)
    student_collection = get_student_collection(student_id)
    global_collection = get_global_collection()

    student_results = student_collection.query(query_embeddings=[query_embedding], n_results=top_k)
    global_results = global_collection.query(query_embeddings=[query_embedding], n_results=top_k)

    docs = []
    if student_results.get("documents"):
        docs.extend(student_results["documents"][0])
    if global_results.get("documents"):
        docs.extend(global_results["documents"][0])

    seen = set()
    unique_docs = [d for d in docs if not (d in seen or seen.add(d))]
    return "\n".join(unique_docs)


def build_prompt(student_id: str, query: str, user=None) -> str:
    """Compose a grounded prompt using RAG context + memory."""
    from .models import ChatHistory

    context = retrieve_context(student_id, query)
    memory = []

    if user is not None and getattr(user, "is_authenticated", False):
        qs = ChatHistory.objects.filter(user=user).order_by('-created_at').values_list('question', 'answer')[:5]
        for q, a in qs:
            memory.append(f"Q: {q}\nA: {a or ''}")

    mem_block = "\n---\n".join(memory)
    system_msg = (
        "You are an academic mentor. Be concise and clear. "
        "Use the context and chat history to answer helpfully."
    )

    return f"{system_msg}\n\nContext:\n{context}\n\nHistory:\n{mem_block}\n\nUser: {query}\nAnswer:"


def generate_stream_with_context(student_id: str, query: str, user=None):
    """Stream AI response with context grounding."""
    prompt = build_prompt(student_id, query, user)
    chunks, full_text = [], ""

    for chunk in client.models.generate_content_stream(
        model=TEXT_MODEL,
        contents=[{"role": "user", "parts": [{"text": prompt}]}],
    ):
        if hasattr(chunk, "text") and chunk.text:
            chunks.append(chunk.text)
            full_text += chunk.text

    return chunks, full_text