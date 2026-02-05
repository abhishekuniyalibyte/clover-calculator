"""
Extractor factory for automatically selecting the right extractor
"""
import pdfplumber
from typing import Optional
import logging

from .base import BaseExtractor
from .chase import ChaseExtractor

logger = logging.getLogger(__name__)


class ExtractorFactory:
    """
    Factory class to automatically detect and instantiate the correct extractor
    """

    @staticmethod
    def create_extractor(file_path: str) -> Optional[BaseExtractor]:
        """
        Detect the processor type and return appropriate extractor

        Args:
            file_path: Path to the PDF file

        Returns:
            Appropriate extractor instance or None if detection fails
        """
        try:
            # Read first page to detect processor
            with pdfplumber.open(file_path) as pdf:
                if not pdf.pages:
                    logger.error("PDF has no pages")
                    return None

                # Extract text from first page
                first_page_text = pdf.pages[0].extract_text() or ""
                text_lower = first_page_text.lower()

                # Detect processor based on keywords
                if 'chase paymentech' in text_lower or 'j.p.morgan' in text_lower:
                    logger.info("Detected Chase Paymentech statement")
                    return ChaseExtractor(file_path)

                elif 'clover' in text_lower:
                    logger.info("Detected Clover statement")
                    # TODO: Implement CloverExtractor
                    logger.warning("Clover extractor not yet implemented")
                    return None

                elif 'square' in text_lower:
                    logger.info("Detected Square statement")
                    # TODO: Implement SquareExtractor
                    logger.warning("Square extractor not yet implemented")
                    return None

                elif 'stripe' in text_lower:
                    logger.info("Detected Stripe statement")
                    # TODO: Implement StripeExtractor
                    logger.warning("Stripe extractor not yet implemented")
                    return None

                elif 'moneris' in text_lower:
                    logger.info("Detected Moneris statement")
                    # TODO: Implement MonerisExtractor
                    logger.warning("Moneris extractor not yet implemented")
                    return None

                else:
                    logger.warning(f"Could not detect processor type from PDF. First 200 chars: {first_page_text[:200]}")
                    return None

        except Exception as e:
            logger.error(f"Error creating extractor: {str(e)}")
            return None

    @staticmethod
    def extract_from_file(file_path: str) -> dict:
        """
        Convenience method to detect processor and extract data in one call

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted data dictionary
        """
        extractor = ExtractorFactory.create_extractor(file_path)

        if not extractor:
            return {
                'success': False,
                'error': 'Could not detect processor type or processor not supported',
                'extraction_confidence': 0
            }

        try:
            data = extractor.extract()
            data['success'] = True
            return data
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'extraction_confidence': 0
            }
