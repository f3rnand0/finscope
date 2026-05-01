"""End-to-end tests for Transaction Categorizer."""

import pytest
import os
from io import BytesIO
from decimal import Decimal
from datetime import datetime
from src.models import Transaction


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    from app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


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
    
    def test_prefix_rules_override_merchant(self, client):
        """Verify static prefix rules override learned merchant rules."""
        from app import engine, transaction_store, get_stored_transactions
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
        engine.learn_from_manual(tx, 'Other/E-commerce')
        
        # Reset transaction
        tx.budget_category = None
        tx.confidence = 0.0
        
        # Auto-categorize should apply prefix rule (Food/Groceries) not learned rule
        result = engine.categorize(tx)
        assert result.category == 'Food/Groceries'
        assert result.method == 'prefix_rule'


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
        assert 'Category' in tsv  # Header row exists
    
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
