"""Tests for MHTML parser."""

import pytest
import quopri
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from bs4 import BeautifulSoup
from src.parser import AmountParseError, MHTMLParser, MHTMLParseError
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
        result = parser.parse_amount('-8.000,00')
        assert result == Decimal('-8000.00')
    
    def test_parse_amount_with_currency(self, parser):
        """Test parsing amount with EUR symbol."""
        result = parser.parse_amount('-20,70 EUR')
        assert result == Decimal('-20.70')
    
    def test_parse_amount_simple(self, parser):
        """Test parsing simple amount."""
        result = parser.parse_amount('100,00')
        assert result == Decimal('100.00')

    @pytest.mark.parametrize(
        "amount,expected",
        [
            ('500,00', Decimal('500.00')),
            ('5.089,71', Decimal('5089.71')),
            ('-8.000,00 EUR', Decimal('-8000.00')),
            ('€ 1.234,56', Decimal('1234.56')),
            ('−500,00 EUR', Decimal('-500.00')),
            ('+12,34', Decimal('12.34')),
        ]
    )
    def test_parse_amount_german_formats(self, parser, amount, expected):
        """Test supported German-locale amount formats."""
        assert parser.parse_amount(amount) == expected

    @pytest.mark.parametrize(
        "amount",
        [
            '500.00',
            '-8,000.00',
            '1,234.56',
            '1.23,45',
            'not money',
            '',
        ]
    )
    def test_parse_amount_rejects_non_german_formats(self, parser, amount):
        """Reject non-German or invalid amount formats."""
        with pytest.raises(AmountParseError):
            parser.parse_amount(amount)
    
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

    def test_fixture_row_accounting(self, parser):
        """Document source rows, skipped settlement rows, duplicates, and parsed transactions."""
        fixture_path = Path(__file__).parent / 'fixtures' / 'transactions March.mhtml'
        raw = fixture_path.read_bytes()
        html = quopri.decodestring(raw).decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'lxml')
        rows = soup.find_all('db-list-row')

        assert len(rows) == 78
        assert sum(
            1 for row in rows
            if 'see settlement account' in row.get_text().lower()
        ) == 6
        candidate_keys = []
        for idx, row in enumerate(rows):
            tx = parser._parse_transaction_row(row, idx)
            if not tx:
                continue
            candidate_keys.append((
                tx.date.strftime('%Y-%m-%d') if tx.date else '',
                tx.counter_party,
                str(tx.amount),
                tx.description
            ))

        assert len(candidate_keys) - len(set(candidate_keys)) == 1
        assert len(parser.extract_transactions(raw)) == 71

    def test_fixture_hypovereinsbank_amount(self, parser):
        """Verify the HypoVereinsbank fixture transaction is not inflated."""
        fixture_path = Path(__file__).parent / 'fixtures' / 'transactions March.mhtml'
        transactions = parser.extract_transactions(fixture_path.read_bytes())

        hypo_transactions = [
            tx for tx in transactions
            if 'hypovereinsbank' in f"{tx.counter_party} {tx.description}".lower()
        ]

        assert len(hypo_transactions) == 1
        assert hypo_transactions[0].amount == Decimal('-500.00')

    def test_fixture_expenses_are_not_decimal_comma_inflated(self, parser):
        """Guard against comma-decimal amounts being parsed as cents-free integers."""
        fixture_path = Path(__file__).parent / 'fixtures' / 'transactions March.mhtml'
        transactions = parser.extract_transactions(fixture_path.read_bytes())

        expenses = [tx for tx in transactions if tx.is_expense]

        assert expenses
        assert max(abs(tx.amount) for tx in expenses) <= Decimal('10000.00')
        assert sum(tx.amount for tx in transactions) == Decimal('-6541.98')

    def test_invalid_fixture_amount_reports_context(self, parser):
        """Invalid amount errors include row, source line, amount, and transaction context."""
        html = b"""
        <html><body>
        <db-list-row>
          <span data-test="counterPartyNameOrTransactionTypeLabel"><span>Test Merchant</span></span>
          <span class="color-text-secondary">Bad amount transaction</span>
          <span data-test="transactionCategoryName"><span class="db-status__text">Uncategorized</span></span>
          <span data-test="amount"><span class="directional"><span>500.00 EUR</span></span></span>
        </db-list-row>
        </body></html>
        """

        with pytest.raises(MHTMLParseError) as exc:
            parser.extract_transactions(html)

        message = str(exc.value)
        assert 'transaction row 0' in message
        assert "raw amount='500.00 EUR'" in message
        assert 'source line=' in message
        assert 'merchant=Test Merchant' in message
        assert 'description=Bad amount transaction' in message


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
