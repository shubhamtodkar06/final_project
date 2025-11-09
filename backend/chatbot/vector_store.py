#backend/chatbot/vector_store.py
import chromadb
from chromadb.config import Settings
import os

# Persistent storage directory for ChromaDB
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

# Global variable to cache the Chroma client
_chroma_client = None

def get_chroma_client():
    """Safely get or create a global ChromaDB client instance."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.Client(Settings(persist_directory=CHROMA_DIR))
    return _chroma_client

def get_student_collection(student_id: str):
    """Return or create a collection for a specific student."""
    client = get_chroma_client()
    return client.get_or_create_collection(name=f"student_{student_id}")

def get_global_collection():
    """Return or create a global resource collection."""
    client = get_chroma_client()
    return client.get_or_create_collection(name="global_resources")