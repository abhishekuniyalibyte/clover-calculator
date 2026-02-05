"""
Base extractor class for PDF statement processing
"""
import pdfplumber
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal
import logging

from .ocr_helper import OCRHelper, check_tesseract_installed

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """
    Abstract base class for PDF extractors
    Each processor (Chase, Clover, Square, etc.) should implement this
    """

    def __init__(self, file_path: str, force_ocr: bool = True):
        """
        Initialize extractor with file path

        Args:
            file_path: Path to the PDF file
            force_ocr: If True, always use OCR instead of pdfplumber (default: True)
        """
        self.file_path = file_path
        self.pdf = None
        self.extracted_data = {}
        self.confidence = 0.0
        self.errors = []
        self.force_ocr = force_ocr

    def extract(self) -> Dict[str, Any]:
        """
        Main extraction method

        Returns:
            Dictionary containing extracted statement data
        """
        try:
            with pdfplumber.open(self.file_path) as pdf:
                self.pdf = pdf

                # Extract text from all pages
                self.full_text = self._extract_full_text()

                # Detect processor type
                processor = self._detect_processor()

                # Extract basic metadata
                self.extracted_data['processor_name'] = processor
                self.extracted_data['merchant_name'] = self._extract_merchant_name()
                self.extracted_data['statement_period'] = self._extract_statement_period()

                # Extract financial data
                self.extracted_data['card_volumes'] = self._extract_card_volumes()
                self.extracted_data['fees'] = self._extract_fees()
                self.extracted_data['totals'] = self._extract_totals()

                # Calculate confidence score
                self.confidence = self._calculate_confidence()
                self.extracted_data['extraction_confidence'] = self.confidence

                # Add raw data for debugging
                self.extracted_data['raw_data'] = {
                    'page_count': len(pdf.pages),
                    'processor': processor,
                    'errors': self.errors
                }

                logger.info(f"Extraction completed for {processor} with confidence {self.confidence}%")

        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            self.errors.append(f"Extraction error: {str(e)}")
            self.extracted_data['extraction_confidence'] = 0
            self.extracted_data['errors'] = self.errors

        return self.extracted_data

    def _extract_full_text(self) -> str:
        """
        Extract all text from PDF
        Uses OCR by default, falls back to pdfplumber if OCR not available
        """
        # Force OCR if enabled
        if self.force_ocr and check_tesseract_installed():
            logger.info("Force extraction enabled. Using text extraction...")
            try:
                ocr_text = OCRHelper.extract_text_from_pdf(self.file_path, dpi=300)
                if len(ocr_text) > 100:
                    logger.info(f"Text extraction completed. Extracted {len(ocr_text)} characters.")
                    self.errors.append("Used LLM-based extraction (force_ocr=True)")
                    return ocr_text
                else:
                    logger.warning(f"Extracted only {len(ocr_text)} chars. Falling back to pdfplumber...")
            except Exception as e:
                logger.error(f"Text extraction failed: {str(e)}. Falling back to pdfplumber...")
                self.errors.append(f"LLM extraction failed: {str(e)}, using pdfplumber")

        # Extract with pdfplumber
        text_parts = []
        for page in self.pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        combined_text = "\n".join(text_parts)

        # If extracted text is too short and extraction not already tried, try alternative extraction
        if len(combined_text.strip()) < 100 and not self.force_ocr:
            logger.warning(f"pdfplumber extracted only {len(combined_text)} chars. Attempting alternative extraction...")

            if check_tesseract_installed():
                try:
                    ocr_text = OCRHelper.extract_text_from_pdf(self.file_path, dpi=300)
                    if len(ocr_text) > len(combined_text):
                        logger.info(f"Alternative extraction got {len(ocr_text)} chars vs pdfplumber's {len(combined_text)} chars.")
                        self.errors.append("Used alternative extraction fallback")
                        return ocr_text
                except Exception as e:
                    logger.error(f"Alternative extraction failed: {str(e)}")
                    self.errors.append(f"Alternative extraction failed: {str(e)}")
            else:
                logger.warning("Alternative extraction not available")
                self.errors.append("Limited text detected but alternative extraction not available")

        return combined_text

    @abstractmethod
    def _detect_processor(self) -> str:
        """
        Detect the payment processor from PDF content
        Should be implemented by each processor-specific extractor
        """
        pass

    @abstractmethod
    def _extract_merchant_name(self) -> str:
        """Extract merchant business name"""
        pass

    @abstractmethod
    def _extract_statement_period(self) -> Dict[str, Optional[str]]:
        """
        Extract statement period dates

        Returns:
            Dict with 'start_date' and 'end_date' keys
        """
        pass

    @abstractmethod
    def _extract_card_volumes(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract card type volumes and transaction counts

        Returns:
            Dict with card types as keys (visa, mastercard, amex, discover, interac)
        """
        pass

    @abstractmethod
    def _extract_fees(self) -> Dict[str, Decimal]:
        """
        Extract fee breakdowns

        Returns:
            Dict with fee types (interchange, assessment, processing, monthly, other)
        """
        pass

    @abstractmethod
    def _extract_totals(self) -> Dict[str, Any]:
        """
        Extract total volumes and transaction counts

        Returns:
            Dict with total_volume and transaction_count
        """
        pass

    def _calculate_confidence(self) -> float:
        """
        Calculate extraction confidence score based on extracted data

        Returns:
            Confidence score between 0-100
        """
        score = 0.0
        max_score = 100.0

        # Merchant name (20 points)
        if self.extracted_data.get('merchant_name'):
            score += 20

        # Statement period (20 points)
        period = self.extracted_data.get('statement_period', {})
        if period.get('start_date') and period.get('end_date'):
            score += 20
        elif period.get('start_date') or period.get('end_date'):
            score += 10

        # Card volumes (30 points)
        volumes = self.extracted_data.get('card_volumes', {})
        if volumes:
            score += 30

        # Fees (20 points)
        fees = self.extracted_data.get('fees', {})
        if fees:
            score += 20

        # Totals (10 points)
        totals = self.extracted_data.get('totals', {})
        if totals.get('total_volume'):
            score += 10

        return min(score, max_score)

    def _safe_decimal(self, value: Any, default: Decimal = Decimal('0.00')) -> Decimal:
        """
        Safely convert value to Decimal

        Args:
            value: Value to convert
            default: Default value if conversion fails

        Returns:
            Decimal value
        """
        if value is None:
            return default

        try:
            # Remove currency symbols, commas, parentheses
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').replace('(', '-').replace(')', '').strip()
            return Decimal(str(value))
        except:
            return default

    def _safe_int(self, value: Any, default: int = 0) -> int:
        """
        Safely convert value to integer

        Args:
            value: Value to convert
            default: Default value if conversion fails

        Returns:
            Integer value
        """
        if value is None:
            return default

        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return int(value)
        except:
            return default
