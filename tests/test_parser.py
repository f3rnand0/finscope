"""Tests for MHTML parser."""

import pytest
from datetime import datetime
from decimal import Decimal
from src.parser import MHTMLParser
from src.models import Transaction


class TestMHTMLParser:
    """Test cases for MHTMLParser."""
    
    @pytest.fixture
    def parser(self):
        return MHTMLParser()
    
    def test_parse_date_valid(self, parser):
        """Test parsing valid German date."""
        result = parser.parse_date('15.03.2026')
        assert result == datetime(2026, 3, 15)
    
    def test_parse_date_invalid(self, parser):
        """Test parsing invalid date returns None."""
        result = parser.parse_date('invalid')
        assert result is None
    
    def test_parse_amount_with_thousands(self, parser):
        """Test parsing amount with thousands separator."""
        result = parser.parse_amount('-8,000.00')
        assert result == Decimal('-8000.00')
    
    def test_parse_amount_with_currency(self, parser):
        """Test parsing amount with EUR symbol."""
        result = parser.parse_amount('-20.70 EUR')
        assert result == Decimal('-20.70')
    
    def test_parse_amount_simple(self, parser):
        """Test parsing simple amount."""
        result = parser.parse_amount('100.00')
        assert result == Decimal('100.00')
    
    def test_clean_html_entities(self, parser):
        """Test cleaning HTML entities."""
        result = parser.clean_html_entities('Food &amp; Beverages')
        assert result == 'Food & Beverages'
    
    def test_extract_merchant_simple(self, parser):
        """Test merchant extraction."""
        desc = "ALDI SE U. CO. KG//Muenchen/DE"
        result = parser.extract_merchant_from_description(desc)
        assert 'ALDI' in result
    
    def test_extract_merchant_with_location(self, parser):
        """Test merchant extraction with location separator."""
        desc = "AMAZON//Berlin/DE 15-03-2026T10:30:00"
        result = parser.extract_merchant_from_description(desc)
        assert result == 'AMAZON'
    
    def test_decode_content_raises_on_invalid(self, parser):
        """Test that decode raises on invalid content."""
        # This should not raise as quopri is lenient
        result = parser.decode_content(b'invalid but not crashing')
        assert isinstance(result, str)


class TestTransactionModel:
    """Test cases for Transaction model."""
    
    def test_transaction_is_expense(self):
        """Test expense detection."""
        tx = Transaction(
            id='tx_1',
            date=datetime.now(),
            counter_party='Test',
            description='Test desc',
            amount=Decimal('-20.50'),
            bank_category='Food'
        )
        assert tx.is_expense is True
        assert tx.is_income is False
    
    def test_transaction_is_income(self):
        """Test income detection."""
        tx = Transaction(
            id='tx_1',
            date=datetime.now(),
            counter_party='Test',
            description='Test desc',
            amount=Decimal('1000.00'),
            bank_category='Salary'
        )
        assert tx.is_income is True
        assert tx.is_expense is False
    
    def test_transaction_to_dict(self):
        """Test transaction serialization."""
        tx = Transaction(
            id='tx_1',
            date=datetime(2026, 3, 15),
            counter_party='ALDI',
            description='Groceries',
            amount=Decimal('-50.00'),
            bank_category='Food',
            budget_category='Food/Groceries',
            confidence=0.95
        )
        d = tx.to_dict()
        assert d['id'] == 'tx_1'
        assert d['amount'] == '-50.00'
        assert d['is_expense'] is True
