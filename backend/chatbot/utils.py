

import google.generativeai as genai
from django.conf import settings
from .vector_store import get_collection

genai.configure(api_key=settings.GEMINI_API_KEY)

EMBED_MODEL = "models/embedding-001"
TEXT_MODEL = "gemini-1.5-flash"

def get_embedding(text: str):
    """Generate embedding vector for text."""
    result = genai.embed_content(model=EMBED_MODEL, content=text)
    return result["embedding"]

def generate_response(prompt: str):
    """Generate AI text response."""
    model = genai.GenerativeModel(TEXT_MODEL)
    response = model.generate_content(prompt)
    return response.text

def rag_query(student_id: str, query: str):
    """Perform Retrieval-Augmented Generation."""
    query_embedding = get_embedding(query)
    collection = get_collection(student_id)
    results = collection.query(query_embeddings=[query_embedding], n_results=3)

    context = "\n".join(results["documents"][0]) if results["documents"] else ""
    prompt = f"Use the following context to answer:\n{context}\n\nQuestion: {query}"

    ai_reply = generate_response(prompt)
    collection.add(
        documents=[query, ai_reply],
        embeddings=[query_embedding],
        ids=[f"q_{student_id}_{len(results.get('ids', [])) + 1}"]
    )
    return ai_reply
import os
import google.generativeai as genai
from django.conf import settings
from .vector_store import get_student_collection, get_global_collection
from .models import Resource

genai.configure(api_key=settings.GEMINI_API_KEY)

EMBED_MODEL = "models/embedding-001"
TEXT_MODEL = "gemini-1.5-flash"

def get_embedding(text: str):
    """Generate embedding vector for text."""
    result = genai.embed_content(model=EMBED_MODEL, content=text)
    return result["embedding"]

def generate_response(prompt: str):
    """Generate AI text response."""
    model = genai.GenerativeModel(TEXT_MODEL)
    response = model.generate_content(prompt)
    return response.text

def index_resource(resource: Resource):
    """
    Index a resource into the vector database for retrieval.
    Stores in both global and user-specific collections.
    """
    # Chunk the content if needed (simple split)
    content = resource.content
    chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]
    embeddings = [get_embedding(chunk) for chunk in chunks]
    ids = [f"resource_{resource.id}_chunk{i}" for i in range(len(chunks))]

    # Store in global collection
    global_collection = get_global_collection()
    global_collection.add(documents=chunks, embeddings=embeddings, ids=ids)

    # Store in student-specific collection if owner exists
    if resource.owner_id:
        student_collection = get_student_collection(str(resource.owner_id))
        student_collection.add(documents=chunks, embeddings=embeddings, ids=ids)

def retrieve_context(student_id: str, query: str, top_k: int = 3):
    """
    Retrieve relevant context from both student-specific and global collections.
    """
    query_embedding = get_embedding(query)
    student_collection = get_student_collection(student_id)
    global_collection = get_global_collection()

    student_results = student_collection.query(query_embeddings=[query_embedding], n_results=top_k)
    global_results = global_collection.query(query_embeddings=[query_embedding], n_results=top_k)
    # Combine and deduplicate documents
    docs = []
    if student_results.get("documents"):
        docs.extend(student_results["documents"][0])
    if global_results.get("documents"):
        docs.extend(global_results["documents"][0])
    # Deduplicate and join
    context = "\n".join(list(dict.fromkeys(docs)))
    return context

def rag_query(student_id: str, query: str):
    """
    Perform Retrieval-Augmented Generation using both personal and global context.
    """
    context = retrieve_context(student_id, query)
    prompt = f"Use the following context to answer the question as helpfully as possible.\n\nContext:\n{context}\n\nQuestion: {query}"
    ai_reply = generate_response(prompt)
    # Optionally, store the chat history in vector db or model
    # Optionally, add the Q&A to student's collection for future retrieval
    student_collection = get_student_collection(student_id)
    query_embedding = get_embedding(query)
    student_collection.add(
        documents=[query, ai_reply],
        embeddings=[query_embedding, get_embedding(ai_reply)],
        ids=[f"q_{student_id}_{os.urandom(6).hex()}_q", f"q_{student_id}_{os.urandom(6).hex()}_a"]
    )
    return ai_reply