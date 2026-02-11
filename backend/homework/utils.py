# backend/homework/utils.py

import re
import json
import logging
import pytesseract
import pdfplumber

from PIL import Image
from core.ai_manager import ai_generate

logger = logging.getLogger(__name__)


# ======================================================
# SCORE NORMALIZATION
# ======================================================

def normalize_score(score):
    """
    Normalize AI score to 0–100 float.

    Accepts:
    - 7/10
    - 8 out of 10
    - 75%
    - 0.75
    - 75
    """
    if score is None:
        return 0.0

    if isinstance(score, (int, float)):
        # Convert decimals like 0.75 -> 75
        if 0 <= score <= 1:
            return round(score * 100, 2)
        return float(score)

    s = str(score).strip().lower()

    # --- "7/10" ---
    if "/" in s:
        try:
            num, den = s.split("/")
            return round((float(num) / float(den)) * 100, 2)
        except Exception:
            return 0.0

    # --- "8 out of 10" ---
    match = re.search(r"(\d+)\s*out\s*of\s*(\d+)", s)
    if match:
        try:
            num, den = float(match.group(1)), float(match.group(2))
            return round((num / den) * 100, 2)
        except Exception:
            return 0.0

    # --- "75%" ---
    if s.endswith("%"):
        try:
            return float(s.replace("%", ""))
        except Exception:
            return 0.0

    # --- fallback numeric ---
    try:
        return float(s)
    except Exception:
        return 0.0


# ======================================================
# CLEAN AI JSON
# ======================================================

def clean_json_response(raw_text: str):
    """
    Cleans and parses AI JSON safely.
    Extracts first valid JSON object even if text surrounds it.
    """

    if not raw_text:
        return {"feedback": "No response from AI.", "score": 0.0}

    # Remove markdown wrappers
    cleaned = re.sub(r"```(?:json)?|```", "", raw_text).strip()

    # ⭐ Attempt to extract first JSON object
    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)

    if json_match:
        cleaned = json_match.group(0)

    # -------- Direct JSON Parse --------
    try:
        data = json.loads(cleaned)

        if isinstance(data, dict):
            return {
                "feedback": str(data.get("feedback", "No feedback found.")),
                "score": normalize_score(data.get("score"))
            }

    except Exception as e:
        logger.warning(f"⚠️ JSON parsing failed: {e}")

    # -------- Regex fallback --------
    feedback_match = re.search(r'"feedback"\s*:\s*"([^"]+)"', cleaned)
    score_match = re.search(r'"score"\s*:\s*("?[^",}]+"?)', cleaned)

    feedback = feedback_match.group(1) if feedback_match else "AI returned unstructured text."
    score = normalize_score(score_match.group(1)) if score_match else 0.0

    return {"feedback": feedback, "score": score}


# ======================================================
# AI HOMEWORK EVALUATION
# ======================================================

def evaluate_homework_with_ai(student_id, text, subject):
    """
    Sends homework text to Gemini for evaluation.
    Returns:
        {
            feedback: str,
            score: float
        }
    """

    logger.info(f"📘 Evaluating homework | student={student_id} | subject={subject}")

    try:
        raw_response = ai_generate(
            student_id=student_id,
            query=f"Evaluate the following {subject} homework:\n{text}",
            mode="homework_feedback",
            subject=subject,
            scope="subject"
        )

        logger.debug(f"🧠 Raw AI Output: {str(raw_response)[:500]}")

        result = clean_json_response(raw_response)

        feedback = result["feedback"]
        score = result["score"]

        # Safety validation
        if not feedback or len(feedback.strip()) < 10:
            feedback = "AI feedback incomplete. Please resubmit homework."

        score = max(0.0, min(100.0, score))

        return {"feedback": feedback, "score": score}

    except Exception as e:
        logger.error(f"❌ Homework AI evaluation failed: {e}")
        return {"feedback": "AI evaluation failed. Try again later.", "score": 0.0}


# ======================================================
# FILE TEXT EXTRACTION
# ======================================================

def extract_text_from_file(file):
    """
    Extract text from uploaded homework files.

    Supports:
    ✔ Text files
    ✔ Images via OCR
    ✔ PDF text extraction
    ✔ OCR fallback for scanned PDFs
    """

    content_type = file.content_type or ""

    try:
        # ---------- TEXT FILE ----------
        if content_type.startswith("text"):
            file.seek(0)
            return file.read().decode("utf-8")

        # ---------- IMAGE OCR ----------
        if content_type.startswith("image"):
            file.seek(0)
            image = Image.open(file)
            return pytesseract.image_to_string(image)

        # ---------- PDF ----------
        if content_type == "application/pdf":
            file.seek(0)
            extracted_text = ""

            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"

            # --- OCR fallback for scanned PDF ---
            if not extracted_text.strip():
                logger.info("PDF text empty. Using OCR fallback.")

                file.seek(0)

                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages:
                        image = page.to_image(resolution=300).original
                        extracted_text += pytesseract.image_to_string(image)

            return extracted_text.strip()

        raise ValueError("Unsupported file type for OCR")

    except Exception as e:
        logger.error(f"❌ File extraction failed: {e}")
        raise