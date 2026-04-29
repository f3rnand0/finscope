"""MHTML parser for Deutsche Bank transaction exports."""

import quopri
import re
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from bs4 import BeautifulSoup

from .models import Transaction


class MHTMLParser:
    """Parser for Deutsche Bank MHTML transaction exports."""
    
    def decode_content(self, content: bytes) -> str:
        """Decode quoted-printable MHTML content."""
        try:
            decoded = quopri.decodestring(content)
            return decoded.decode('utf-8', errors='ignore')
        except Exception as e:
            raise ValueError(f"Failed to decode MHTML content: {e}")
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string in multiple formats."""
        if not date_str:
            return None
        date_str = date_str.strip()
        formats = ['%d.%m.%Y', '%m/%d/%Y', '%d-%m-%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    
    def parse_amount(self, amount_str: str) -> Decimal:
        """Parse amount string (standard format with dot decimal separator)."""
        if not amount_str:
            return Decimal('0')
        # Remove currency symbols and whitespace
        cleaned = amount_str.strip().replace('EUR', '').replace('€', '').strip()
        # Remove thousand separators (commas), keep decimal point
        cleaned = cleaned.replace(',', '')
        try:
            return Decimal(cleaned)
        except Exception:
            return Decimal('0')
    
    def clean_html_entities(self, text: str) -> str:
        """Clean HTML entities from text."""
        if not text:
            return ''
        # Basic HTML entity decoding
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        text = text.replace('&nbsp;', ' ')
        return text.strip()
    
    def extract_merchant_from_description(self, description: str) -> str:
        """Extract merchant name from transaction description."""
        if not description:
            return ''
        
        # Remove extra whitespace and newlines
        desc = ' '.join(description.split())
        
        # Extract before // (location separator)
        if '//' in desc:
            merchant_part = desc.split('//')[0].strip()
        else:
            merchant_part = desc
        
        # Extract company name (usually first part in CAPS or Title Case)
        # Remove common suffixes
        suffixes = [
            ' GMBH', ' SE', ' U. CO. KG', ' AG', ' OHG', ' GBR',
            ' FIL.', ' E.K.', ' LTD', ' INC', ' LLC'
        ]
        
        merchant = merchant_part
        for suffix in suffixes:
            if suffix in merchant.upper():
                # Keep the suffix but stop after it
                idx = merchant.upper().find(suffix)
                if idx > 0:
                    end_idx = idx + len(suffix)
                    merchant = merchant[:end_idx].strip()
                    break
        
        # If still long, take first significant part
        if len(merchant) > 50:
            parts = merchant.split()
            merchant = ' '.join(parts[:3]) if len(parts) > 3 else merchant
        
        return merchant[:60].strip()
    
    def _extract_date_from_label(self, row) -> Optional[datetime]:
        """Try to extract date from a parent cirrus-date-group-label."""
        try:
            # Look for a preceding cirrus-date-group-label in the DOM
            label = row.find_parent('ul')
            if label:
                prev_div = label.find_previous_sibling('div')
                if prev_div:
                    date_label = prev_div.find('cirrus-date-group-label')
                    if date_label:
                        date_text = date_label.get_text(strip=True)
                        return self.parse_date(date_text)
        except Exception:
            pass
        return None

    def _extract_date_from_row(self, row) -> Optional[datetime]:
        """Try to extract date from within the row itself."""
        # Look for dot-separated dates in row text
        date_elem = row.find(string=re.compile(r'\d{2}\.\d{2}\.\d{4}'))
        if date_elem:
            date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', str(date_elem))
            if date_match:
                return self.parse_date(date_match.group(1))
        # Look for dash-separated dates in descriptions
        desc_elem = row.find(class_=re.compile('color-text-secondary'))
        if desc_elem:
            desc_text = desc_elem.get_text()
            dash_match = re.search(r'(\d{2}-\d{2}-\d{4})', desc_text)
            if dash_match:
                return self.parse_date(dash_match.group(1))
        return None

    def extract_transactions(self, content: bytes) -> List[Transaction]:
        """Extract transactions from MHTML content."""
        html = self.decode_content(content)
        soup = BeautifulSoup(html, 'lxml')

        transactions = []
        seen = set()
        transaction_rows = soup.find_all('db-list-row')

        for idx, row in enumerate(transaction_rows):
            try:
                tx = self._parse_transaction_row(row, idx)
                if tx:
                    # Deduplicate by key fields
                    key = (tx.date.strftime('%Y-%m-%d') if tx.date else '',
                           tx.counter_party, str(tx.amount), tx.description)
                    if key not in seen:
                        seen.add(key)
                        transactions.append(tx)
            except Exception as e:
                # Log error but continue processing other transactions
                print(f"Error parsing transaction {idx}: {e}")
                continue

        return transactions

    def _parse_transaction_row(self, row, idx: int) -> Optional[Transaction]:
        """Parse a single transaction row."""
        # Skip settlement account rows (not real transactions)
        row_text = row.get_text().lower()
        if 'see settlement account' in row_text:
            return None

        # Extract date - try date group label first, then row content
        date = self._extract_date_from_label(row)
        if not date:
            date = self._extract_date_from_row(row)
        
        # Extract counter party / transaction type
        counter_party_elem = row.find(attrs={'data-test': 'counterPartyNameOrTransactionTypeLabel'})
        counter_party = ''
        if counter_party_elem:
            span = counter_party_elem.find('span')
            if span:
                counter_party = self.clean_html_entities(span.get_text(strip=True))
        
        # Extract description (from secondary text)
        desc_elem = row.find(class_=re.compile('color-text-secondary'))
        description = ''
        if desc_elem:
            description = self.clean_html_entities(desc_elem.get_text(strip=True))
        
        # If no description found, try counter party description
        if not description and counter_party_elem:
            description = counter_party
        
        # Extract bank category
        category_elem = row.find(attrs={'data-test': 'transactionCategoryName'})
        bank_category = 'Uncategorized'
        if category_elem:
            status_text = category_elem.find(class_='db-status__text')
            if status_text:
                bank_category = self.clean_html_entities(status_text.get_text(strip=True))
        
        # Extract amount
        amount_elem = row.find(attrs={'data-test': 'amount'})
        amount = Decimal('0')
        if amount_elem:
            # Look for directional amount (has negative/positive class)
            directional = amount_elem.find(class_='directional')
            if directional:
                amount_text = directional.get_text(strip=True)
                amount = self.parse_amount(amount_text)
            else:
                # Fallback to any number in the amount element
                amount_text = amount_elem.get_text(strip=True)
                amount = self.parse_amount(amount_text)
        
        # Generate transaction ID
        tx_id = f"tx_{idx}_{date.strftime('%Y%m%d') if date else 'unknown'}"
        
        return Transaction(
            id=tx_id,
            date=date or datetime.now(),
            counter_party=counter_party,
            description=description,
            amount=amount,
            bank_category=bank_category
        )
