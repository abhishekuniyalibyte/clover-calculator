"""
LLM helper for extracting and structuring data from PDFs using LLaMA 4 Maverick via Groq API
"""
import logging
from typing import List, Optional
from pathlib import Path
import os
from django.conf import settings

try:
    from groq import Groq
    import pdfplumber
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

logger = logging.getLogger(__name__)


class OCRHelper:
    """
    Helper class for LLM-based PDF extraction using LLaMA 4 Maverick via Groq
    """

    _groq_client = None

    @staticmethod
    def get_groq_client():
        """Get or create Groq client (singleton pattern)"""
        if OCRHelper._groq_client is None:
            api_key = getattr(settings, 'GROQ_API_KEY', os.getenv('GROQ_API_KEY'))
            if not api_key:
                logger.error("GROQ_API_KEY not found in settings or environment")
                return None
            logger.info("Initializing Groq client...")
            OCRHelper._groq_client = Groq(api_key=api_key)
        return OCRHelper._groq_client

    @staticmethod
    def is_available() -> bool:
        """Check if LLM dependencies are installed"""
        return LLM_AVAILABLE and OCRHelper.get_groq_client() is not None

    @staticmethod
    def extract_text_from_pdf(pdf_path: str, dpi: int = 300) -> str:
        """
        Extract text from PDF using pdfplumber

        Args:
            pdf_path: Path to PDF file
            dpi: DPI for image conversion (not used, kept for compatibility)

        Returns:
            Extracted text from all pages
        """
        if not LLM_AVAILABLE:
            logger.error("Required dependencies not installed. Install groq and pdfplumber.")
            return ""

        try:
            logger.info(f"Starting text extraction from PDF: {pdf_path}")

            full_text = []
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    logger.info(f"Processing page {page_num + 1}/{len(pdf.pages)}...")
                    text = page.extract_text()
                    if text:
                        full_text.append(text)

            combined_text = "\n\n=== PAGE BREAK ===\n\n".join(full_text)
            logger.info(f"Text extraction completed. Extracted {len(combined_text)} characters.")

            return combined_text

        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            return ""

    @staticmethod
    def extract_text_from_image(image_path: str) -> str:
        """
        Extract text from image file (not supported without OCR)

        Args:
            image_path: Path to image file

        Returns:
            Empty string (images require OCR which is not available)
        """
        logger.warning("Image extraction not supported with LLM-only approach. Use PDF files instead.")
        return ""

    @staticmethod
    def extract_with_layout(pdf_path: str, dpi: int = 300) -> List[dict]:
        """
        Extract text with layout information (not supported)

        Args:
            pdf_path: Path to PDF file
            dpi: DPI for image conversion

        Returns:
            Empty list (layout extraction not supported)
        """
        logger.warning("Layout extraction not supported with LLM approach")
        return []


def check_llm_installed() -> bool:
    """
    Check if LLM is available and API key is configured

    Returns:
        True if LLM is available, False otherwise
    """
    if not LLM_AVAILABLE:
        return False

    try:
        client = OCRHelper.get_groq_client()
        return client is not None
    except Exception as e:
        logger.warning(f"LLM is not properly configured: {str(e)}")
        return False


# Keep old function name for backward compatibility
def check_tesseract_installed() -> bool:
    """
    Backward compatibility function - now checks LLM instead

    Returns:
        True if LLM is available, False otherwise
    """
    return check_llm_installed()
