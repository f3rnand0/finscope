"""Tests for exporter module."""

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
                budget_category='Income/Job salary',
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
        
        assert 'Income/Job salary' in aggregated
        assert aggregated['Income/Job salary']['count'] == 1
        assert aggregated['Income/Job salary']['total'] == Decimal('5089.71')
        
        assert 'Food/Groceries' in aggregated
        assert aggregated['Food/Groceries']['count'] == 2
        assert aggregated['Food/Groceries']['total'] == Decimal('-77.70')
    
    def test_export_to_tsv(self, exporter, sample_transactions):
        """Test TSV export."""
        tsv = exporter.export_to_tsv(sample_transactions)

        assert 'Category\tSubcategory\tActual Spent\tDescription\tTransaction Count' in tsv
        assert 'Income' in tsv
        assert 'Job salary' in tsv
        assert 'Food' in tsv
        assert 'Groceries' in tsv
        assert '€77.70' in tsv or '€45.20' in tsv  # Amount should be present
        assert 'Budget' not in tsv.split('\n')[0]
        assert 'Variance' not in tsv.split('\n')[0]
        assert 'ALDI##' in tsv  # Merchant##Description format
    
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
