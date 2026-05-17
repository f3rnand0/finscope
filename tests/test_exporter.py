"""Tests for exporter module."""

import csv
import io
import pytest
from datetime import datetime
from decimal import Decimal
from src.exporter import BudgetExporter
from src.models import Transaction


class TestBudgetExporter:
    """Test cases for BudgetExporter."""
    
    @pytest.fixture
    def exporter(self):
        return BudgetExporter()
    
    @pytest.fixture
    def sample_transactions(self):
        """Create sample transactions for testing."""
        return [
            Transaction(
                id='tx_1',
                date=datetime(2026, 3, 1),
                counter_party='Employer',
                description='Monthly Salary',
                amount=Decimal('5089.71'),
                bank_category='Salary / Wages',
                budget_category='Income/Job Salary',
                confidence=0.95
            ),
            Transaction(
                id='tx_2',
                date=datetime(2026, 3, 2),
                counter_party='ALDI',
                description='ALDI SE U. CO. KG//Muenchen/DE',
                amount=Decimal('-45.20'),
                bank_category='Food / Beverages',
                budget_category='Food/Groceries',
                confidence=0.9
            ),
            Transaction(
                id='tx_3',
                date=datetime(2026, 3, 3),
                counter_party='ALDI',
                description='ALDI SE U. CO. KG//Muenchen/DE',
                amount=Decimal('-32.50'),
                bank_category='Food / Beverages',
                budget_category='Food/Groceries',
                confidence=0.9
            ),
            Transaction(
                id='tx_4',
                date=datetime(2026, 3, 4),
                counter_party='Unknown',
                description='Some unknown transaction',
                amount=Decimal('-20.00'),
                bank_category='Uncategorized',
                budget_category=None,
                confidence=0.0
            )
        ]
    
    def test_aggregate_by_category(self, exporter, sample_transactions):
        """Test aggregation by category."""
        aggregated = exporter.aggregate_by_category(sample_transactions)
        
        assert 'Income/Job Salary' in aggregated
        assert aggregated['Income/Job Salary']['count'] == 1
        assert aggregated['Income/Job Salary']['total'] == Decimal('5089.71')
        
        assert 'Food/Groceries' in aggregated
        assert aggregated['Food/Groceries']['count'] == 2
        assert aggregated['Food/Groceries']['total'] == Decimal('-77.70')
    
    def test_export_to_tsv(self, exporter, sample_transactions):
        """Test TSV export."""
        tsv = exporter.export_to_tsv(sample_transactions)
        rows = list(csv.reader(io.StringIO(tsv), delimiter='\t'))
        header = rows[0]

        assert header == ['Category / Expense', 'Budget', 'Actual Spent', 'Budget vs. Actual']
        assert 'Description' not in header
        assert 'Transaction Count' not in header
        assert 'Subcategory' not in header
        assert rows[1][0] == 'Home Expenses'
        assert any(row[0] == '- Geiger Edelmetalle' for row in rows)
        assert 'Job Salary' not in tsv

        groceries = next(row for row in rows if row[0] == '- Groceries')
        assert groceries == ['- Groceries', '€550.00', '€77.70', '€472.30']

        dining_out = next(row for row in rows if row[0] == '- Dining Out')
        assert dining_out == ['- Dining Out', '€150.00', '', '€150.00']

    def test_export_maps_legacy_categories_to_template_rows(self, exporter):
        """Old stored categories should still land in the current template row."""
        transactions = [
            Transaction(
                id='tx_1',
                date=datetime(2026, 3, 1),
                counter_party='Amazon',
                description='Amazon purchase',
                amount=Decimal('-50.00'),
                bank_category='Online Shopping',
                budget_category='Other/E-commerce',
                confidence=0.9
            ),
            Transaction(
                id='tx_2',
                date=datetime(2026, 3, 2),
                counter_party='TF Bank',
                description='Credit card payment',
                amount=Decimal('-25.00'),
                bank_category='Uncategorized',
                budget_category='Debt/Credit Card TF Bank',
                confidence=0.9
            )
        ]

        rows = list(csv.reader(io.StringIO(exporter.export_to_tsv(transactions)), delimiter='\t'))
        credit_card = next(row for row in rows if row[0] == '- Expenses with credit card (TF Bank)')

        assert credit_card == ['- Expenses with credit card (TF Bank)', '€400.00', '€75.00', '€325.00']

    def test_zero_variance_is_blank(self, exporter):
        """Variance should be blank when actual equals budget."""
        transactions = [
            Transaction(
                id='tx_1',
                date=datetime(2026, 3, 1),
                counter_party='Geiger Edelmetalle',
                description='Geiger Edelmetalle AG',
                amount=Decimal('-100.00'),
                bank_category='Uncategorized',
                budget_category='Investments/Geiger Edelmetalle',
                confidence=0.9
            )
        ]

        rows = list(csv.reader(io.StringIO(exporter.export_to_tsv(transactions)), delimiter='\t'))
        geiger = next(row for row in rows if row[0] == '- Geiger Edelmetalle')

        assert geiger == ['- Geiger Edelmetalle', '€100.00', '€100.00', '']
    
    def test_get_summary(self, exporter, sample_transactions):
        """Test summary statistics."""
        summary = exporter.get_summary(sample_transactions)

        assert summary['total_transactions'] == 4
        assert summary['categorized_count'] == 3
        assert summary['uncategorized_count'] == 1
        assert summary['total_income'] == Decimal('5089.71')
        assert summary['total_expenses'] == Decimal('97.70')

    def test_excluded_transactions_filtered(self, exporter, sample_transactions):
        """Test that excluded transactions are filtered from export."""
        sample_transactions[1].excluded = True
        summary = exporter.get_summary(sample_transactions)
        assert summary['total_transactions'] == 3

        aggregated = exporter.aggregate_by_category(sample_transactions)
        assert aggregated['Food/Groceries']['count'] == 1
        assert aggregated['Food/Groceries']['total'] == Decimal('-32.50')
    
    def test_export_transactions_list(self, exporter, sample_transactions):
        """Test detailed transaction list export."""
        tsv = exporter.export_transactions_list(sample_transactions)
        
        assert 'Date\tDescription\tAmount' in tsv
        assert 'ALDI' in tsv
        assert 'Salary' in tsv
