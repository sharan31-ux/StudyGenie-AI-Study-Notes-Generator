"""
PDF text extraction utilities for StudyGenie.
Handles multi-page PDFs, skips unreadable pages gracefully, and reports
basic document stats used elsewhere in the app.
"""

from typing import Tuple
from pypdf import PdfReader
from pypdf.errors import PdfReadError


def extract_text_from_pdf(uploaded_file) -> Tuple[str, int]:
    """
    Extract raw text from a Streamlit UploadedFile (or any file-like object).

    Returns:
        (full_text, num_pages)
    """
    try:
        reader = PdfReader(uploaded_file)
    except PdfReadError as e:
        raise ValueError(f"Could not read this PDF (it may be corrupted or encrypted): {e}")

    if getattr(reader, "is_encrypted", False):
        try:
            reader.decrypt("")
        except Exception:
            raise ValueError(
                "This PDF is password-protected. Please upload an unlocked PDF."
            )

    num_pages = len(reader.pages)
    page_texts = []

    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        page_texts.append(page_text)

    full_text = "\n\n".join(page_texts).strip()
    return full_text, num_pages


def estimate_reading_stats(text: str) -> dict:
    """Rough stats to show the user (word count, estimated reading time)."""
    words = len(text.split())
    reading_minutes = max(1, round(words / 200))
    return {"word_count": words, "reading_minutes": reading_minutes}
