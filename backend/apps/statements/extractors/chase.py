"""
Chase/JP Morgan statement extractor
"""
import re
from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class ChaseExtractor(BaseExtractor):
    """
    Extractor for Chase Paymentech merchant statements
    """

    def _detect_processor(self) -> str:
        """Detect if this is a Chase statement"""
        # Look for Chase branding in the text
        text_lower = self.full_text.lower()

        if 'chase paymentech' in text_lower or 'j.p.morgan' in text_lower or 'chase merchant services' in text_lower:
            return 'Chase Paymentech'

        return 'Unknown'

    def _extract_merchant_name(self) -> str:
        """Extract merchant name from Chase statement"""
        try:
            # Chase statements typically have merchant name at the top
            # Pattern: company name appears before ATTN: or on first few lines
            lines = self.full_text.split('\n')

            for i, line in enumerate(lines[:15]):  # Check first 15 lines
                # Skip header lines
                if 'Merchant Services' in line or 'PO Box' in line or 'CHASE' in line:
                    continue

                # Look for ATTN: pattern
                if 'ATTN:' in line:
                    # Merchant name is usually on the previous line
                    if i > 0:
                        merchant_name = lines[i - 1].strip()
                        if merchant_name and len(merchant_name) > 3:
                            return merchant_name

                # Look for company name pattern (all caps, reasonable length)
                if line.isupper() and 5 < len(line) < 100 and 'NOTICE' not in line:
                    # Check if it looks like a company name (has INC, LLC, LTD, CORP, etc.)
                    if any(suffix in line for suffix in ['INC', 'LLC', 'LTD', 'CORP', 'CO.']):
                        return line.strip()

            # Fallback: look for "Company Number" line and grab previous meaningful line
            for i, line in enumerate(lines):
                if 'Company Number' in line and i > 0:
                    for j in range(i - 1, max(0, i - 5), -1):
                        potential_name = lines[j].strip()
                        if potential_name and len(potential_name) > 3 and 'Statement Period' not in potential_name:
                            return potential_name

        except Exception as e:
            logger.error(f"Error extracting merchant name: {str(e)}")
            self.errors.append(f"Merchant name extraction error: {str(e)}")

        return ''

    def _extract_statement_period(self) -> Dict[str, Optional[str]]:
        """Extract statement period from Chase statement"""
        try:
            # Pattern: "Statement Period 1-Jun-2024 - 30-Jun-2024"
            pattern = r'Statement Period\s+(\d{1,2}-[A-Za-z]{3}-\d{4})\s*-\s*(\d{1,2}-[A-Za-z]{3}-\d{4})'
            match = re.search(pattern, self.full_text)

            if match:
                start_str = match.group(1)
                end_str = match.group(2)

                # Parse dates
                start_date = self._parse_chase_date(start_str)
                end_date = self._parse_chase_date(end_str)

                return {
                    'start_date': start_date,
                    'end_date': end_date
                }

        except Exception as e:
            logger.error(f"Error extracting statement period: {str(e)}")
            self.errors.append(f"Statement period extraction error: {str(e)}")

        return {'start_date': None, 'end_date': None}

    def _parse_chase_date(self, date_str: str) -> Optional[str]:
        """
        Parse Chase date format (e.g., '1-Jun-2024') to ISO format (YYYY-MM-DD)

        Args:
            date_str: Date string in Chase format

        Returns:
            Date string in ISO format or None
        """
        try:
            # Parse format like '1-Jun-2024'
            dt = datetime.strptime(date_str, '%d-%b-%Y')
            return dt.strftime('%Y-%m-%d')
        except:
            try:
                # Try alternative format
                dt = datetime.strptime(date_str, '%d-%B-%Y')
                return dt.strftime('%Y-%m-%d')
            except:
                return None

    def _extract_card_volumes(self) -> Dict[str, Dict[str, Any]]:
        """Extract card type volumes from Chase statement"""
        card_volumes = {
            'visa': {'volume': Decimal('0.00'), 'count': 0},
            'mastercard': {'volume': Decimal('0.00'), 'count': 0},
            'amex': {'volume': Decimal('0.00'), 'count': 0},
            'discover': {'volume': Decimal('0.00'), 'count': 0},
            'interac': {'volume': Decimal('0.00'), 'count': 0},
        }

        try:
            # First, try parsing from text (more reliable when tables fail)
            lines = self.full_text.split('\n')

            for line in lines:
                line_upper = line.upper()

                # Pattern: "VISA* 98 $73,239.99" or "VISA 98 73,239.99"
                # Look for card type followed by count and amount

                if 'VISA' in line_upper and 'MASTERCARD' not in line_upper:
                    match = re.search(r'VISA[*\s]+(\d+)[*\s]+\$?\s?([\d,]+\.\d{2})', line, re.IGNORECASE)
                    if match:
                        card_volumes['visa']['count'] = self._safe_int(match.group(1))
                        card_volumes['visa']['volume'] = self._safe_decimal(match.group(2))
                        logger.info(f"Found VISA from text: {match.group(1)} transactions, ${match.group(2)}")

                elif 'MASTERCARD' in line_upper:
                    match = re.search(r'MASTERCARD[*\s]+(\d+)[*\s]+\$?\s?([\d,]+\.\d{2})', line, re.IGNORECASE)
                    if match:
                        card_volumes['mastercard']['count'] = self._safe_int(match.group(1))
                        card_volumes['mastercard']['volume'] = self._safe_decimal(match.group(2))
                        logger.info(f"Found MASTERCARD from text: {match.group(1)} transactions, ${match.group(2)}")

                elif 'AMERICAN EXPRESS' in line_upper or ('AMEX' in line_upper and 'EXPRESS' not in line_upper):
                    match = re.search(r'(?:AMERICAN EXPRESS|AMEX)[*\s]+(\d+)[*\s]+\$?\s?([\d,]+\.\d{2})', line, re.IGNORECASE)
                    if match:
                        card_volumes['amex']['count'] = self._safe_int(match.group(1))
                        card_volumes['amex']['volume'] = self._safe_decimal(match.group(2))
                        logger.info(f"Found AMEX from text: {match.group(1)} transactions, ${match.group(2)}")

                elif 'DISCOVER' in line_upper:
                    match = re.search(r'DISCOVER[*\s]+(\d+)[*\s]+\$?\s?([\d,]+\.\d{2})', line, re.IGNORECASE)
                    if match:
                        card_volumes['discover']['count'] = self._safe_int(match.group(1))
                        card_volumes['discover']['volume'] = self._safe_decimal(match.group(2))
                        logger.info(f"Found DISCOVER from text: {match.group(1)} transactions, ${match.group(2)}")

                elif 'INTERAC' in line_upper:
                    match = re.search(r'INTERAC[*\s]+(\d+)[*\s]+\$?\s?([\d,]+\.\d{2})', line, re.IGNORECASE)
                    if match:
                        card_volumes['interac']['count'] = self._safe_int(match.group(1))
                        card_volumes['interac']['volume'] = self._safe_decimal(match.group(2))
                        logger.info(f"Found INTERAC from text: {match.group(1)} transactions, ${match.group(2)}")

            # If text parsing didn't work, fallback to table extraction
            if all(v['volume'] == Decimal('0.00') for v in card_volumes.values()):
                logger.info("Text parsing failed, trying table extraction...")
                for page in self.pdf.pages:
                    tables = page.extract_tables()

                    for table in tables:
                        if not table:
                            continue

                        # Look for Card Type Summary table
                        for i, row in enumerate(table):
                            if not row:
                                continue

                            # Check if this is a card type row
                            if row[0]:
                                card_type = str(row[0]).upper().strip()

                                # Map to our card types
                                if 'VISA' in card_type and 'MASTERCARD' not in card_type:
                                    self._parse_card_row(row, card_volumes['visa'])
                                elif 'MASTERCARD' in card_type:
                                    self._parse_card_row(row, card_volumes['mastercard'])
                                elif 'AMERICAN EXPRESS' in card_type or 'AMEX' in card_type:
                                    self._parse_card_row(row, card_volumes['amex'])
                                elif 'DISCOVER' in card_type:
                                    self._parse_card_row(row, card_volumes['discover'])
                                elif 'INTERAC' in card_type:
                                    self._parse_card_row(row, card_volumes['interac'])

        except Exception as e:
            logger.error(f"Error extracting card volumes: {str(e)}")
            self.errors.append(f"Card volumes extraction error: {str(e)}")

        return card_volumes

    def _parse_card_row(self, row: list, card_data: dict):
        """
        Parse a card type row from the table

        Chase format: [Card Type, Number of Sales, Sales, Number of Credits, Credits, Total Number of Items, Net Sales, Average Ticket]
        """
        try:
            # Sales amount is typically in column 2
            if len(row) > 2 and row[2]:
                sales = self._safe_decimal(row[2])
                card_data['volume'] += sales

            # Number of sales is in column 1
            if len(row) > 1 and row[1]:
                count = self._safe_int(row[1])
                card_data['count'] += count

            # Net sales might be in column 6
            if len(row) > 6 and row[6]:
                net_sales = self._safe_decimal(row[6])
                # Use net sales if it's different (accounts for credits)
                if net_sales != Decimal('0.00'):
                    card_data['volume'] = net_sales

        except Exception as e:
            logger.warning(f"Error parsing card row: {str(e)}")

    def _extract_fees(self) -> Dict[str, Decimal]:
        """Extract fee breakdowns from Chase statement"""
        fees = {
            'interchange_fees': Decimal('0.00'),
            'assessment_fees': Decimal('0.00'),
            'processing_fees': Decimal('0.00'),
            'monthly_fees': Decimal('0.00'),
            'other_fees': Decimal('0.00'),
        }

        try:
            # Look for fee sections in the text
            lines = self.full_text.split('\n')

            for i, line in enumerate(lines):
                line_upper = line.upper()

                # Interchange fees
                if 'INTERCHANGE FEES TOTAL' in line_upper:
                    # Extract amount from the line or next line
                    amount = self._extract_amount_from_line(line)
                    if amount:
                        fees['interchange_fees'] += amount

                # Assessment fees
                elif 'ASSESSMENT FEES' in line_upper and 'TOTAL' not in line_upper:
                    amount = self._extract_amount_from_line(line)
                    if amount:
                        fees['assessment_fees'] += amount

                elif 'FEES AND ASSESSMENTS TOTAL' in line_upper:
                    # This includes assessment + transaction fees
                    amount = self._extract_amount_from_line(line)
                    if amount:
                        # Split between assessment and processing
                        fees['assessment_fees'] += amount / 2
                        fees['processing_fees'] += amount / 2

                # Monthly/admin fees
                elif 'MONTHLY ADMIN FEE' in line_upper or 'MONTHLY FEE' in line_upper:
                    amount = self._extract_amount_from_line(line)
                    if amount:
                        fees['monthly_fees'] += amount

                # Other charges
                elif 'OTHER CHARGES' in line_upper or 'TOTAL OTHER CHARGES' in line_upper:
                    amount = self._extract_amount_from_line(line)
                    if amount:
                        fees['other_fees'] += amount

            # Alternative: extract from tables
            for page in self.pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue

                    for row in table:
                        if not row or len(row) < 2:
                            continue

                        row_text = ' '.join([str(cell) for cell in row if cell]).upper()

                        if 'INTERCHANGE FEES TOTAL' in row_text:
                            amount = self._extract_amount_from_row(row)
                            if amount:
                                fees['interchange_fees'] = max(fees['interchange_fees'], amount)

        except Exception as e:
            logger.error(f"Error extracting fees: {str(e)}")
            self.errors.append(f"Fees extraction error: {str(e)}")

        return fees

    def _extract_totals(self) -> Dict[str, Any]:
        """Extract total volumes and counts from Chase statement"""
        totals = {
            'total_volume': Decimal('0.00'),
            'transaction_count': 0,
            'total_fees': Decimal('0.00'),
        }

        try:
            # First, try parsing from text
            lines = self.full_text.split('\n')

            for line in lines:
                line_upper = line.upper()

                # Pattern: "Totals 165 $146,718.43" or similar
                if 'TOTALS' in line_upper or 'TOTAL' in line_upper:
                    # Look for pattern: word followed by number and amount
                    match = re.search(r'TOTALS?[*\s]+(\d+)[*\s]+\$?\s?([\d,]+\.\d{2})', line, re.IGNORECASE)
                    if match:
                        totals['transaction_count'] = self._safe_int(match.group(1))
                        totals['total_volume'] = self._safe_decimal(match.group(2))
                        logger.info(f"Found totals from text: {match.group(1)} transactions, ${match.group(2)}")

                # Look for "Total Amount Charged"
                if 'TOTAL AMOUNT CHARGED' in line_upper:
                    amount = self._extract_amount_from_line(line)
                    if amount:
                        totals['total_fees'] = amount
                        logger.info(f"Found total fees from text: ${amount}")

            # If text parsing didn't work, fallback to table extraction
            if totals['total_volume'] == Decimal('0.00'):
                logger.info("Text parsing for totals failed, trying table extraction...")
                for page in self.pdf.pages:
                    tables = page.extract_tables()

                    for table in tables:
                        if not table:
                            continue

                        for row in table:
                            if not row:
                                continue

                            # Look for "Totals" row
                            if row[0] and 'TOTALS' in str(row[0]).upper():
                                # Net sales is typically in column 6
                                if len(row) > 6 and row[6]:
                                    totals['total_volume'] = self._safe_decimal(row[6])

                                # Total items is in column 5
                                if len(row) > 5 and row[5]:
                                    totals['transaction_count'] = self._safe_int(row[5])

                            # Look for "Total Amount Charged"
                            if row[0] and 'TOTAL AMOUNT CHARGED' in str(row[0]).upper():
                                if len(row) > 1 and row[-1]:  # Last column usually has the amount
                                    totals['total_fees'] = self._safe_decimal(row[-1])

        except Exception as e:
            logger.error(f"Error extracting totals: {str(e)}")
            self.errors.append(f"Totals extraction error: {str(e)}")

        return totals

    def _extract_amount_from_line(self, line: str) -> Optional[Decimal]:
        """
        Extract dollar amount from a text line

        Args:
            line: Text line containing amount

        Returns:
            Decimal amount or None
        """
        try:
            # Pattern for amounts like $1,234.56 or $1234.56
            pattern = r'\$\s?([\d,]+\.\d{2})'
            match = re.search(pattern, line)

            if match:
                return self._safe_decimal(match.group(1))

            # Try without dollar sign
            pattern = r'([\d,]+\.\d{2})'
            matches = re.findall(pattern, line)
            if matches:
                # Return the last match (usually the total)
                return self._safe_decimal(matches[-1])

        except Exception as e:
            logger.warning(f"Error extracting amount from line: {str(e)}")

        return None

    def _extract_amount_from_row(self, row: list) -> Optional[Decimal]:
        """Extract dollar amount from a table row"""
        try:
            # Look for amount in last few columns
            for cell in reversed(row):
                if cell:
                    amount = self._safe_decimal(cell)
                    if amount > 0:
                        return amount
        except:
            pass

        return None
