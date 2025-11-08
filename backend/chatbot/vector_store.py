

import chromadb
from chromadb.config import Settings

# Initialize persistent ChromaDB client
chroma_client = chromadb.Client(
    Settings(persist_directory="chatbot/chroma_db")
)

def get_collection(student_id: str):
    """Return or create a collection for a specific student."""
    return chroma_client.get_or_create_collection(name=f"student_{student_id}")
import chromadb
from chromadb.config import Settings
import os

# Persistent storage directory for ChromaDB
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

# Initialize persistent ChromaDB client
chroma_client = chromadb.Client(Settings(persist_directory=CHROMA_DIR))

def get_student_collection(student_id: str):
    """Return or create a collection for a specific student."""
    return chroma_client.get_or_create_collection(name=f"student_{student_id}")

def get_global_collection():
    """Return or create a global resource collection."""
    return chroma_client.get_or_create_collection(name="global_resources")