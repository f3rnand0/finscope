"""Smart transaction categorization with learning capability."""

import json
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .models import Transaction, CategorizationResult
from config import DEFAULT_BANK_MAPPINGS, PREFIX_RULES_PATH, CONTAINS_RULES_PATH


class CategorizationRules:
    """Manages persistent categorization rules."""
    
    def __init__(self, config_path: str = 'config/categorization_rules.json'):
        self.config_path = Path(config_path)
        self.merchant_rules: Dict[str, dict] = {}
        self.keyword_rules: Dict[str, dict] = {}
        self.bank_mappings: Dict[str, str] = dict(DEFAULT_BANK_MAPPINGS)
        self.manual_rules: list = []
        self.prefix_rules: Dict[str, List[str]] = {}
        self.contains_rules: Dict[str, List[str]] = {}
        self._load_rules()
    
    def _load_rules(self):
        """Load rules from JSON files."""
        # Load learned rules
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.merchant_rules = data.get('merchant_rules', {})
                    self.keyword_rules = data.get('keyword_rules', {})
                    self.bank_mappings.update(data.get('bank_mappings', {}))
                    self.manual_rules = data.get('manual_rules', [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load rules: {e}")
        
        # Load static prefix rules
        prefix_path = Path(PREFIX_RULES_PATH)
        if prefix_path.exists():
            try:
                with open(prefix_path, 'r', encoding='utf-8') as f:
                    self.prefix_rules = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load prefix rules: {e}")
        
        # Load static contains rules
        contains_path = Path(CONTAINS_RULES_PATH)
        if contains_path.exists():
            try:
                with open(contains_path, 'r', encoding='utf-8') as f:
                    self.contains_rules = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load contains rules: {e}")
    
    def save_rules(self):
        """Save learned rules to JSON file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'version': '1.0.0',
            'last_updated': datetime.now().isoformat(),
            'merchant_rules': self.merchant_rules,
            'keyword_rules': self.keyword_rules,
            'bank_mappings': self.bank_mappings,
            'manual_rules': self.manual_rules
        }
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save rules: {e}")
    
    def add_merchant_rule(self, merchant: str, category: str):
        """Add or update a merchant rule."""
        merchant = merchant.upper().strip()
        if merchant in self.merchant_rules:
            # Update existing rule
            self.merchant_rules[merchant]['count'] += 1
            # Recalculate confidence based on count
            count = self.merchant_rules[merchant]['count']
            self.merchant_rules[merchant]['confidence'] = min(0.5 + (count * 0.05), 0.95)
        else:
            # New rule with base confidence
            self.merchant_rules[merchant] = {
                'category': category,
                'confidence': 0.8,
                'count': 1
            }
        self.save_rules()
    
    def add_keyword_rule(self, keyword: str, category: str):
        """Add or update a keyword rule."""
        keyword = keyword.upper().strip()
        if keyword in self.keyword_rules:
            self.keyword_rules[keyword]['count'] = self.keyword_rules[keyword].get('count', 1) + 1
        else:
            self.keyword_rules[keyword] = {
                'category': category,
                'confidence': 0.6,
                'count': 1
            }
        self.save_rules()
    
    def get_category_for_merchant(self, merchant: str) -> Optional[Tuple[str, float]]:
        """Get category for a merchant if known."""
        if not merchant:
            return None
        
        merchant_upper = merchant.upper().strip()
        
        # Exact match
        if merchant_upper in self.merchant_rules:
            rule = self.merchant_rules[merchant_upper]
            return (rule['category'], rule['confidence'])
        
        # Partial match (merchant contains known pattern)
        for pattern, rule in self.merchant_rules.items():
            if pattern in merchant_upper or merchant_upper in pattern:
                # Lower confidence for partial match
                confidence = rule['confidence'] * 0.8
                return (rule['category'], confidence)
        
        return None
    
    def get_category_for_keyword(self, text: str) -> Optional[Tuple[str, float]]:
        """Get category based on keyword in text."""
        if not text:
            return None
        
        text_upper = text.upper()
        
        for keyword, rule in self.keyword_rules.items():
            if keyword in text_upper:
                return (rule['category'], rule['confidence'])
        
        return None
    
    def get_category_for_bank_category(self, bank_category: str) -> Optional[str]:
        """Get budget category from bank category mapping."""
        return self.bank_mappings.get(bank_category)
    
    def get_category_for_prefix(self, description: str) -> Optional[Tuple[str, float]]:
        """Get category based on prefix match in description."""
        if not description:
            return None
        
        desc_upper = description.upper().strip()
        
        for category, prefixes in self.prefix_rules.items():
            for prefix in prefixes:
                if desc_upper.startswith(prefix.upper()):
                    return (category, 0.95)
        
        return None
    
    def get_category_for_contains(self, description: str) -> Optional[Tuple[str, float]]:
        """Get category based on text contains match in description."""
        if not description:
            return None
        
        desc_upper = description.upper()
        
        for category, texts in self.contains_rules.items():
            for text in texts:
                if text.upper() in desc_upper:
                    return (category, 0.90)
        
        return None


class CategorizationEngine:
    """Engine for categorizing transactions with learning."""
    
    def __init__(self, config_path: str = 'config/categorization_rules.json'):
        self.rules = CategorizationRules(config_path)
    
    def extract_merchant(self, description: str) -> str:
        """Extract merchant name from transaction description."""
        if not description:
            return ''
        
        # Remove extra whitespace
        desc = ' '.join(description.split())
        
        # Extract before // (location separator)
        if '//' in desc:
            merchant_part = desc.split('//')[0].strip()
        else:
            merchant_part = desc
        
        # Clean up common suffixes and take main company name
        # Pattern: Company names often in first part, may have GMBH, SE, etc.
        
        # Remove trailing dates and transaction details
        merchant_part = re.sub(r'\d{2}-\d{2}-\d{4}T\d{2}:\d{2}:\d{2}.*', '', merchant_part)
        merchant_part = re.sub(r'Folgenr\. \d+.*', '', merchant_part)
        merchant_part = re.sub(r'Verfalld\. \d+.*', '', merchant_part)
        
        # Extract main company name (usually first 2-3 words)
        words = merchant_part.split()
        if len(words) <= 3:
            return merchant_part.strip()[:50]
        
        # Look for known company suffixes
        suffixes = ['GMBH', 'SE', 'AG', 'OHG', 'GBR', 'LTD', 'INC', 'LLC', 'KG']
        for i, word in enumerate(words):
            if any(suffix in word.upper() for suffix in suffixes):
                # Take up to and including the word with suffix
                return ' '.join(words[:i+1]).strip()[:50]
        
        # Default: take first 3 words
        return ' '.join(words[:3]).strip()[:50]
    
    def categorize(self, transaction: Transaction) -> CategorizationResult:
        """Categorize a single transaction."""
        # Priority 1: Static prefix rules (override learned rules)
        match = self.rules.get_category_for_prefix(transaction.description)
        if match:
            category, confidence = match
            return CategorizationResult(category, confidence, 'prefix_rule')
        
        # Priority 2: Static contains rules
        match = self.rules.get_category_for_contains(transaction.description)
        if match:
            category, confidence = match
            return CategorizationResult(category, confidence, 'contains_rule')
        
        # Priority 3: Merchant match
        merchant = self.extract_merchant(transaction.description)
        if merchant:
            match = self.rules.get_category_for_merchant(merchant)
            if match:
                category, confidence = match
                return CategorizationResult(category, confidence, 'merchant')
        
        # Priority 4: Keyword match in description
        match = self.rules.get_category_for_keyword(transaction.description)
        if match:
            category, confidence = match
            return CategorizationResult(category, confidence, 'keyword')
        
        # Priority 5: Bank category mapping
        if transaction.bank_category:
            mapped = self.rules.get_category_for_bank_category(transaction.bank_category)
            if mapped:
                return CategorizationResult(mapped, 0.5, 'bank_mapping')
        
        # No match found
        return CategorizationResult(None, 0.0, 'none')
    
    def learn_from_manual(self, transaction: Transaction, category: str):
        """Learn from manual categorization."""
        merchant = self.extract_merchant(transaction.description)
        
        if merchant and len(merchant) >= 3:
            # Add merchant rule
            self.rules.add_merchant_rule(merchant, category)
        else:
            # Add keyword rule from description
            # Extract significant words (2+ chars, not common words)
            words = transaction.description.upper().split()
            common_words = {'GMBH', 'SE', 'AG', 'DE', 'DER', 'DIE', 'DAS', 'UND', 'VON', 'AUF', 'IN'}
            
            for word in words:
                word = re.sub(r'[^A-Z]', '', word)  # Remove non-letters
                if len(word) >= 4 and word not in common_words:
                    self.rules.add_keyword_rule(word, category)
                    break  # Just add the first significant keyword
    
    def apply_categorization(self, transaction: Transaction, result: CategorizationResult):
        """Apply categorization result to transaction."""
        transaction.budget_category = result.category
        transaction.confidence = result.confidence
    
    def auto_categorize_all(self, transactions: list) -> list:
        """Auto-categorize all transactions."""
        for tx in transactions:
            if not tx.budget_category:  # Only categorize uncategorized
                result = self.categorize(tx)
                self.apply_categorization(tx, result)
        return transactions
