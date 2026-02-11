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

def extract_text_from_file(file):
    """
    Extract text from uploaded homework files.

    Supports:
    ✔ Text files
    ✔ Images via OCR
    ✔ PDF text extraction
    ✔ OCR fallback for scanned PDFs
    """

    content_type = getattr(file, "content_type", "") or ""
    logger.info(
        f"🔍 Starting file extraction | filename={getattr(file, 'name', None)} | content_type={content_type}"
    )

    try:
        # ---------- TEXT FILE ----------
        if content_type.startswith("text"):
            file.seek(0)
            text = file.read().decode("utf-8", errors="ignore")
            logger.info("✅ Text file extracted successfully")
            return text.strip()

        # ---------- IMAGE OCR ----------
        if content_type.startswith("image"):
            file.seek(0)
            image = Image.open(file)
            text = pytesseract.image_to_string(image)
            logger.info("✅ Image OCR completed")
            return text.strip()

        # ---------- PDF ----------
        if content_type == "application/pdf":
            file.seek(0)
            extracted_text = ""

            import pdfplumber
            with pdfplumber.open(file) as pdf:
                logger.info(f"📄 PDF opened | pages={len(pdf.pages)}")
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"

            # --- OCR fallback for scanned PDF ---
            if not extracted_text.strip():
                logger.info("📄 PDF text empty. Using OCR fallback.")

                file.seek(0)

                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages:
                        image = page.to_image(resolution=300).original
                        extracted_text += pytesseract.image_to_string(image)

            logger.info("✅ PDF extraction completed")
            return extracted_text.strip()

        logger.warning(f"⚠️ Unsupported file type: {content_type}")
        raise ValueError("Unsupported file type for OCR")

    except Exception as e:
        logger.error(f"❌ File extraction failed: {e}")
        raise

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