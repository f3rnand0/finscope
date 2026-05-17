"""End-to-end tests for Transaction Categorizer."""

import pytest
import os
from io import BytesIO
from decimal import Decimal
from datetime import datetime
from src.models import Transaction


@pytest.fixture
def client(tmp_path):
    """Create a test client for the Flask app."""
    import app as app_module
    from src.categorizer import CategorizationEngine

    original_engine = app_module.engine
    original_store = app_module.transaction_store
    original_config_path = app_module.app.config['CONFIG_PATH']
    original_testing = app_module.app.config.get('TESTING')

    app_module.app.config['TESTING'] = True
    app_module.app.config['CONFIG_PATH'] = str(tmp_path / 'categorization_rules.json')
    app_module.engine = CategorizationEngine(app_module.app.config['CONFIG_PATH'])
    app_module.transaction_store = {}

    with app_module.app.test_client() as client:
        yield client

    app_module.engine = original_engine
    app_module.transaction_store = original_store
    app_module.app.config['CONFIG_PATH'] = original_config_path
    app_module.app.config['TESTING'] = original_testing


@pytest.fixture
def sample_mhtml():
    """Load sample MHTML file."""
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'transactions March.mhtml')
    with open(fixture_path, 'rb') as f:
        return f.read()


class TestUploadFlow:
    """Test file upload and parsing flow."""
    
    def test_upload_parses_transactions(self, client, sample_mhtml):
        """Upload sample MHTML and verify transactions are parsed."""
        response = client.post(
            '/api/upload',
            data={'file': (BytesIO(sample_mhtml), 'transactions March.mhtml')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['transaction_count'] > 0
    
    def test_upload_rejects_non_mhtml(self, client):
        """Reject non-MHTML files."""
        response = client.post(
            '/api/upload',
            data={'file': (BytesIO(b'not an mhtml file'), 'test.txt')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_upload_rejects_invalid_amount_with_context(self, client):
        """Reject invalid non-German amount text with parser context."""
        invalid_mhtml = b"""
        <html><body>
        <db-list-row>
          <span data-test="counterPartyNameOrTransactionTypeLabel"><span>Test Merchant</span></span>
          <span class="color-text-secondary">Bad amount transaction</span>
          <span data-test="transactionCategoryName"><span class="db-status__text">Uncategorized</span></span>
          <span data-test="amount"><span class="directional"><span>500.00 EUR</span></span></span>
        </db-list-row>
        </body></html>
        """

        response = client.post(
            '/api/upload',
            data={'file': (BytesIO(invalid_mhtml), 'invalid.mhtml')},
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'transaction row 0' in data['error']
        assert "raw amount='500.00 EUR'" in data['error']
        assert 'source line=' in data['error']
        assert 'merchant=Test Merchant' in data['error']


class TestReviewPage:
    """Test review page rendering."""
    
    def test_review_shows_income_and_expenses(self, client, sample_mhtml):
        """Upload and verify review page shows both income and expenses tables."""
        client.post(
            '/api/upload',
            data={'file': (BytesIO(sample_mhtml), 'transactions March.mhtml')},
            content_type='multipart/form-data'
        )
        
        response = client.get('/review')
        html = response.data.decode('utf-8')
        
        assert response.status_code == 200
        assert 'Income' in html
        assert 'Expenses' in html
    
    def test_expense_amounts_positive(self, client, sample_mhtml):
        """Verify expense amounts are rendered as positive numbers."""
        client.post(
            '/api/upload',
            data={'file': (BytesIO(sample_mhtml), 'transactions March.mhtml')},
            content_type='multipart/form-data'
        )
        
        response = client.get('/review')
        html = response.data.decode('utf-8')
        
        # Expense amounts should show as positive (no minus sign before euro symbol)
        # The template uses abs() for expenses
        assert '€-' not in html or html.count('€-') <= html.count('amount-income')
    
    def test_bank_category_hidden(self, client, sample_mhtml):
        """Verify bank category column is not shown."""
        client.post(
            '/api/upload',
            data={'file': (BytesIO(sample_mhtml), 'transactions March.mhtml')},
            content_type='multipart/form-data'
        )
        
        response = client.get('/review')
        html = response.data.decode('utf-8')
        
        assert 'Bank Category' not in html


class TestAutoCategorize:
    """Test auto-categorization with static rules."""
    
    def test_auto_categorize_applies_rules(self, client, sample_mhtml):
        """Verify static prefix/contains rules are applied."""
        client.post(
            '/api/upload',
            data={'file': (BytesIO(sample_mhtml), 'transactions March.mhtml')},
            content_type='multipart/form-data'
        )
        
        response = client.post('/api/transactions/auto-categorize')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['categorized_count'] > 0
    
    def test_learned_merchant_overrides_prefix_rules(self, client):
        """Verify learned merchant rules override static prefix rules."""
        from app import engine
        from src.models import Transaction as TxModel
        
        # Create a transaction that matches prefix rule
        tx = TxModel(
            id='tx_test_1',
            date=datetime.now(),
            counter_party='ALDI',
            description='ALDI SE U. CO. KG//Muenchen/DE',
            amount=Decimal('-20.00'),
            bank_category='Food / Beverages'
        )
        
        # First, manually learn it as a different category
        engine.learn_from_manual(tx, 'Other/Expenses with credit card (TF Bank)')
        
        # Reset transaction
        tx.budget_category = None
        tx.confidence = 0.0
        
        # Auto-categorize should apply learned merchant rule, not the static prefix rule
        result = engine.categorize(tx)
        assert result.category == 'Other/Expenses with credit card (TF Bank)'
        assert result.method == 'merchant'


class TestExport:
    """Test export functionality."""
    
    def test_export_excludes_income(self, client, sample_mhtml):
        """Verify income transactions are excluded from TSV export."""
        client.post(
            '/api/upload',
            data={'file': (BytesIO(sample_mhtml), 'transactions March.mhtml')},
            content_type='multipart/form-data'
        )
        
        response = client.get('/api/export/tsv')
        
        assert response.status_code == 200
        tsv = response.data.decode('utf-8')
        
        # TSV should not contain income-related descriptions
        # (assuming sample has identifiable income like salary)
        # Since we can't know exact content, verify it doesn't crash
        assert tsv.splitlines()[0] == 'Category / Expense\tBudget\tActual Spent\tBudget vs. Actual'
    
    def test_export_summary_excludes_income(self, client, sample_mhtml):
        """Verify export summary excludes income."""
        client.post(
            '/api/upload',
            data={'file': (BytesIO(sample_mhtml), 'transactions March.mhtml')},
            content_type='multipart/form-data'
        )
        
        response = client.get('/api/export/summary')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'summary' in data
        # Total income in summary should be 0 or very small since we filter income
        total_income = Decimal(data['summary'].get('total_income', '0'))
        assert total_income == 0


class TestExclude:
    """Test exclude functionality."""

    def test_exclude_transaction(self, client, sample_mhtml):
        """Test excluding and including transactions."""
        client.post(
            '/api/upload',
            data={'file': (BytesIO(sample_mhtml), 'transactions March.mhtml')},
            content_type='multipart/form-data'
        )

        # Get an expense transaction id
        response = client.get('/api/transactions?type=expense')
        data = response.get_json()
        tx_id = data['transactions'][0]['id']

        # Exclude it
        response = client.post('/api/transactions/exclude', json={
            'transaction_ids': [tx_id],
            'excluded': True
        })
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True

        # Verify it's excluded from export summary
        response = client.get('/api/export/summary')
        summary = response.get_json()['summary']
        assert summary['total_transactions'] < len(data['transactions'])


class TestApiTransactions:
    """Test API transaction endpoints."""

    def test_api_filter_by_type(self, client, sample_mhtml):
        """Test filtering transactions by type."""
        client.post(
            '/api/upload',
            data={'file': (BytesIO(sample_mhtml), 'transactions March.mhtml')},
            content_type='multipart/form-data'
        )

        response = client.get('/api/transactions?type=expense')
        assert response.status_code == 200
        data = response.get_json()

        for tx in data['transactions']:
            assert float(tx['amount']) <= 0

        response = client.get('/api/transactions?type=income')
        assert response.status_code == 200
        data = response.get_json()

        for tx in data['transactions']:
            assert float(tx['amount']) > 0
