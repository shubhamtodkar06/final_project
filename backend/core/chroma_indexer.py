# backend/core/chroma_indexer.py
import logging
from langchain.schema import Document
from core.ai_manager import vectorstore
from student_notes.models import MasterNote, AINote
from resources.models import Resource

logger = logging.getLogger(__name__)


def index_master_notes():
    docs = []
    for note in MasterNote.objects.all():
        docs.append(
            Document(
                page_content=note.content,
                metadata={
                    "grade": note.standard.grade,
                    "subject": note.subject.name,
                    "topic": note.topic.name,
                    "source": note.source,
                    "doc_type": "note",
                }
            )
        )
    if docs:
        vectorstore.add_documents(docs)
        logger.info(f"Indexed {len(docs)} master notes")


def index_ai_notes():
    docs = []
    for note in AINote.objects.all():
        docs.append(
            Document(
                page_content=note.content,
                metadata={
                    "grade": note.standard.grade,
                    "subject": note.subject.name,
                    "topic": note.topic.name if note.topic else None,
                    "source": "ai",
                    "doc_type": "note",
                }
            )
        )
    if docs:
        vectorstore.add_documents(docs)
        logger.info(f"Indexed {len(docs)} AI notes")


def index_resources():
    docs = []
    for r in Resource.objects.all():
        docs.append(
            Document(
                page_content=r.extracted_text or r.content,
                metadata={
                    "grade": r.grade_level,
                    "subject": r.subject,
                    "topic": r.topic,
                    "source": r.type,
                    "doc_type": "resource",
                }
            )
        )
    if docs:
        vectorstore.add_documents(docs)
        logger.info(f"Indexed {len(docs)} resources")


def reindex_all():
    """
    Safe reindex (call manually or via admin command)
    """
    index_master_notes()
    index_ai_notes()
    index_resources()