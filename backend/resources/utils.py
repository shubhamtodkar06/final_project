#backend/resources/utils.py
# backend/resources/utils.py
import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from sentence_transformers import SentenceTransformer
from django.conf import settings
from .models import Resource
import logging

logger = logging.getLogger(__name__)

# Load embedding model once
embedding_model = SentenceTransformer('all-mpnet-base-v2')

def extract_text_from_file(file_path):
    """Extract text from uploaded image or PDF."""
    try:
        ext = os.path.splitext(file_path)[1].lower()
        text = ""
        if ext in ['.png', '.jpg', '.jpeg']:
            text = pytesseract.image_to_string(Image.open(file_path))
        elif ext == '.pdf':
            images = convert_from_path(file_path)
            for img in images:
                text += pytesseract.image_to_string(img)
        else:
            logger.warning(f"Unsupported file type: {ext}")
        return text.strip()
    except Exception as e:
        logger.error(f"Error during OCR: {e}")
        return ""

def generate_embeddings(text):
    """Generate vector embeddings for text content."""
    if not text:
        return []
    try:
        return embedding_model.encode(text)
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return []

def save_extracted_text(resource: Resource):
    """Extract text from file (if any) and store it in the resource model."""
    if not resource.file:
        return

    file_path = resource.file.path
    extracted = extract_text_from_file(file_path)
    resource.extracted_text = extracted
    resource.save()
    logger.info(f"Extracted text saved for resource {resource.id}")

def ingest_resource(user, title, content, subject, grade_level, file=None, type="system"):
    """Create a new resource and optionally process embeddings."""
    resource = Resource.objects.create(
        uploaded_by=user,
        title=title,
        content=content,
        subject=subject,
        grade_level=grade_level,
        type=type,
        file=file
    )

    # Extract text from uploaded file
    if file:
        save_extracted_text(resource)

    # Optionally generate embeddings for RAG
    embeddings = generate_embeddings(resource.content or resource.extracted_text)
    logger.info(f"Embeddings generated for resource {resource.title}: {len(embeddings)} dimensions")

    return resource