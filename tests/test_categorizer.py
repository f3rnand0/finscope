"""Tests for categorizer module."""

import pytest
import json
import tempfile
import os
from datetime import datetime
from decimal import Decimal
from src.categorizer import CategorizationEngine, CategorizationRules
from src.models import Transaction, CategorizationResult


class TestCategorizationRules:
    """Test cases for CategorizationRules."""
    
    @pytest.fixture
    def temp_config(self):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'merchant_rules': {
                    'ALDI': {'category': 'Food/Groceries', 'confidence': 0.95, 'count': 10}
                },
                'keyword_rules': {
                    'TELEKOM': {'category': 'Utilities/Cell Phones', 'confidence': 0.9}
                }
            }, f)
            return f.name
    
    def test_load_rules(self, temp_config):
        """Test loading rules from file."""
        rules = CategorizationRules(temp_config)
        assert 'ALDI' in rules.merchant_rules
        assert rules.merchant_rules['ALDI']['category'] == 'Food/Groceries'
        os.unlink(temp_config)
    
    def test_add_merchant_rule_new(self, temp_config):
        """Test adding new merchant rule."""
        rules = CategorizationRules(temp_config)
        rules.add_merchant_rule('AMAZON', 'Other/Expenses with credit card (TF Bank)')
        assert 'AMAZON' in rules.merchant_rules
        assert rules.merchant_rules['AMAZON']['category'] == 'Other/Expenses with credit card (TF Bank)'
        os.unlink(temp_config)
    
    def test_add_merchant_rule_update(self, temp_config):
        """Test updating existing merchant rule."""
        rules = CategorizationRules(temp_config)
        initial_count = rules.merchant_rules['ALDI']['count']
        rules.add_merchant_rule('ALDI', 'Food/Groceries')
        assert rules.merchant_rules['ALDI']['count'] == initial_count + 1
        os.unlink(temp_config)
    
    def test_get_category_for_merchant_exact(self, temp_config):
        """Test exact merchant match."""
        rules = CategorizationRules(temp_config)
        result = rules.get_category_for_merchant('ALDI')
        assert result is not None
        assert result[0] == 'Food/Groceries'
        assert result[1] == 0.95
        os.unlink(temp_config)
    
    def test_get_category_for_merchant_partial(self, temp_config):
        """Test partial merchant match."""
        rules = CategorizationRules(temp_config)
        result = rules.get_category_for_merchant('ALDI SE U. CO. KG')
        assert result is not None
        assert result[0] == 'Food/Groceries'
        assert result[1] < 0.95  # Lower confidence for partial match
        os.unlink(temp_config)
    
    def test_get_category_for_bank_category(self, temp_config):
        """Test bank category mapping."""
        rules = CategorizationRules(temp_config)
        result = rules.get_category_for_bank_category('Lebensmittel / Getränke')
        assert result == 'Food/Groceries'


class TestCategorizationEngine:
    """Test cases for CategorizationEngine."""
    
    @pytest.fixture
    def engine(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'merchant_rules': {
                    'ALDI': {'category': 'Food/Groceries', 'confidence': 0.95, 'count': 10},
                    'AMAZON': {'category': 'Other/Expenses with credit card (TF Bank)', 'confidence': 0.9, 'count': 5}
                }
            }, f)
            config_path = f.name
        
        engine = CategorizationEngine(config_path)
        yield engine
        os.unlink(config_path)
    
    def test_extract_merchant_simple(self, engine):
        """Test merchant extraction."""
        desc = "ALDI SE U. CO. KG//Muenchen/DE"
        result = engine.extract_merchant(desc)
        assert 'ALDI' in result
    
    def test_extract_merchant_with_date(self, engine):
        """Test merchant extraction with date in description."""
        desc = "AMAZON//Berlin/DE 15-03-2026T10:30:00"
        result = engine.extract_merchant(desc)
        assert result == 'AMAZON'
    
    def test_categorize_by_merchant(self, engine):
        """Test categorization by merchant."""
        tx = Transaction(
            id='tx_1',
            date=datetime.now(),
            counter_party='ALDI',
            description='ALDI SE U. CO. KG//Muenchen/DE',
            amount=Decimal('-20.00'),
            bank_category='Lebensmittel / Getränke'
        )
        result = engine.categorize(tx)
        assert result.category == 'Food/Groceries'
        assert result.method == 'prefix_rule'
        assert result.confidence > 0.5  # Prefix rule has high confidence

    def test_categorize_by_bank_mapping(self, engine):
        """Test categorization by bank category mapping."""
        tx = Transaction(
            id='tx_1',
            date=datetime.now(),
            counter_party='Unknown',
            description='Some transaction',
            amount=Decimal('-50.00'),
            bank_category='Lebensmittel / Getränke'
        )
        result = engine.categorize(tx)
        assert result.category == 'Food/Groceries'
        assert result.method == 'bank_mapping'

    def test_categorize_uncategorized(self, engine):
        """Test uncategorized transaction."""
        tx = Transaction(
            id='tx_1',
            date=datetime.now(),
            counter_party='Unknown',
            description='Unknown merchant XYZ123',
            amount=Decimal('-10.00'),
            bank_category='Unkategorisiert'
        )
        result = engine.categorize(tx)
        assert result.category is None
        assert result.confidence == 0.0
    
    def test_learn_from_manual(self, engine):
        """Test learning from manual categorization."""
        tx = Transaction(
            id='tx_1',
            date=datetime.now(),
            counter_party='NEWSTORE',
            description='NEWSTORE GMBH//Munich/DE',
            amount=Decimal('-30.00'),
            bank_category='Uncategorized'
        )
        engine.learn_from_manual(tx, 'Other/Clothing')
        
        # Should now categorize correctly
        result = engine.categorize(tx)
        assert result.category == 'Other/Clothing'
