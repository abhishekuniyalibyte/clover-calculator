"""
Business logic for statement processing
"""
import logging
import json
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from django.core.files.base import File

from .models import MerchantStatement, StatementData
from .extractors.factory import ExtractorFactory

logger = logging.getLogger(__name__)


def decimal_to_str(obj):
    """
    Convert Decimal objects to strings for JSON serialization
    """
    if isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: decimal_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_str(item) for item in obj]
    return obj


class StatementProcessingService:
    """
    Service class for processing uploaded statements
    """

    @staticmethod
    def process_uploaded_statement(statement: MerchantStatement) -> bool:
        """
        Process an uploaded PDF statement

        Args:
            statement: MerchantStatement instance to process

        Returns:
            True if processing succeeded, False otherwise
        """
        if not statement.file:
            logger.error(f"Statement {statement.id} has no file")
            statement.status = 'FAILED'
            statement.extraction_notes = 'No file attached to statement'
            statement.save()
            return False

        try:
            # Update status to processing
            statement.status = 'PROCESSING'
            statement.save()

            # Get file path
            file_path = statement.file.path

            # Extract data using factory
            logger.info(f"Starting extraction for statement {statement.id} from {file_path}")
            extracted_data = ExtractorFactory.extract_from_file(file_path)

            if not extracted_data.get('success', False):
                # Extraction failed
                error_msg = extracted_data.get('error', 'Unknown extraction error')
                logger.error(f"Extraction failed for statement {statement.id}: {error_msg}")

                statement.status = 'FAILED'
                statement.extraction_notes = error_msg
                statement.extraction_confidence = 0
                statement.save()
                return False

            # Update statement with extracted metadata
            StatementProcessingService._update_statement_metadata(statement, extracted_data)

            # Create or update StatementData
            StatementProcessingService._create_statement_data(statement, extracted_data)

            # Mark as completed
            statement.status = 'COMPLETED'
            statement.processed_at = timezone.now()
            statement.save()

            logger.info(f"Successfully processed statement {statement.id} with confidence {statement.extraction_confidence}%")
            return True

        except Exception as e:
            logger.error(f"Error processing statement {statement.id}: {str(e)}", exc_info=True)
            statement.status = 'FAILED'
            statement.extraction_notes = f"Processing error: {str(e)}"
            statement.save()
            return False

    @staticmethod
    def _update_statement_metadata(statement: MerchantStatement, extracted_data: dict):
        """
        Update statement instance with extracted metadata

        Args:
            statement: MerchantStatement instance
            extracted_data: Extracted data dictionary
        """
        # Merchant name
        if extracted_data.get('merchant_name'):
            statement.merchant_name = extracted_data['merchant_name']

        # Processor name
        if extracted_data.get('processor_name'):
            statement.processor_name = extracted_data['processor_name']

        # Statement period
        period = extracted_data.get('statement_period', {})
        if period.get('start_date'):
            try:
                statement.statement_period_start = datetime.strptime(
                    period['start_date'], '%Y-%m-%d'
                ).date()
            except Exception as e:
                logger.warning(f"Error parsing start date: {str(e)}")

        if period.get('end_date'):
            try:
                statement.statement_period_end = datetime.strptime(
                    period['end_date'], '%Y-%m-%d'
                ).date()
            except Exception as e:
                logger.warning(f"Error parsing end date: {str(e)}")

        # Extraction confidence
        confidence = extracted_data.get('extraction_confidence', 0)
        statement.extraction_confidence = Decimal(str(confidence))

        # Requires review if confidence is low
        statement.requires_review = confidence < 80

        # Extraction notes
        errors = extracted_data.get('raw_data', {}).get('errors', [])
        if errors:
            statement.extraction_notes = '; '.join(errors)

        statement.save()

    @staticmethod
    def _create_statement_data(statement: MerchantStatement, extracted_data: dict):
        """
        Create or update StatementData from extracted data

        Args:
            statement: MerchantStatement instance
            extracted_data: Extracted data dictionary
        """
        # Get totals
        totals = extracted_data.get('totals', {})
        total_volume = totals.get('total_volume', Decimal('0.00'))
        transaction_count = totals.get('transaction_count', 0)

        # Get card volumes
        card_volumes = extracted_data.get('card_volumes', {})
        visa_data = card_volumes.get('visa', {})
        mc_data = card_volumes.get('mastercard', {})
        amex_data = card_volumes.get('amex', {})
        discover_data = card_volumes.get('discover', {})
        interac_data = card_volumes.get('interac', {})

        # Get fees
        fees = extracted_data.get('fees', {})

        # Calculate effective rate if we have volume
        effective_rate = None
        if total_volume and total_volume > 0:
            total_fees = totals.get('total_fees', Decimal('0.00'))
            if total_fees > 0:
                effective_rate = (total_fees / total_volume) * 100

        # Create or update StatementData
        statement_data, created = StatementData.objects.update_or_create(
            statement=statement,
            defaults={
                'total_volume': total_volume,
                'transaction_count': transaction_count,

                # Card volumes
                'visa_volume': visa_data.get('volume', Decimal('0.00')),
                'visa_count': visa_data.get('count', 0),
                'mastercard_volume': mc_data.get('volume', Decimal('0.00')),
                'mastercard_count': mc_data.get('count', 0),
                'amex_volume': amex_data.get('volume', Decimal('0.00')),
                'amex_count': amex_data.get('count', 0),
                'discover_volume': discover_data.get('volume', Decimal('0.00')),
                'discover_count': discover_data.get('count', 0),
                'interac_volume': interac_data.get('volume', Decimal('0.00')),
                'interac_count': interac_data.get('count', 0),

                # Fees
                'interchange_fees': fees.get('interchange_fees', Decimal('0.00')),
                'assessment_fees': fees.get('assessment_fees', Decimal('0.00')),
                'processing_fees': fees.get('processing_fees', Decimal('0.00')),
                'monthly_fees': fees.get('monthly_fees', Decimal('0.00')),
                'other_fees': fees.get('other_fees', Decimal('0.00')),

                # Rate
                'effective_rate': effective_rate,

                # Raw data for debugging (convert Decimals to strings)
                'raw_data': decimal_to_str(extracted_data)
            }
        )

        logger.info(f"{'Created' if created else 'Updated'} StatementData for statement {statement.id}")
