"""Data models for Transaction Categorizer."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Transaction:
    """Represents a single bank transaction."""
    id: str
    date: datetime
    counter_party: str
    description: str
    amount: Decimal
    bank_category: str
    budget_category: Optional[str] = None
    confidence: float = 0.0
    
    @property
    def is_expense(self) -> bool:
        """Check if this is an expense (negative amount)."""
        return self.amount < 0
    
    @property
    def is_income(self) -> bool:
        """Check if this is income (positive amount)."""
        return self.amount > 0
    
    @property
    def merchant(self) -> Optional[str]:
        """Extract merchant name from description (lazy property)."""
        # Simple extraction - will be enhanced by categorizer
        if not self.description:
            return None
        # Take first part before // or first 30 chars
        desc = self.description.split('//')[0].strip()
        return desc[:50] if desc else None
    
    def to_dict(self) -> dict:
        """Convert transaction to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'counter_party': self.counter_party,
            'description': self.description,
            'amount': str(self.amount),
            'bank_category': self.bank_category,
            'budget_category': self.budget_category,
            'confidence': self.confidence,
            'is_expense': self.is_expense
        }


@dataclass
class CategorizationResult:
    """Result of categorization attempt."""
    category: Optional[str]
    confidence: float
    method: str  # 'merchant', 'keyword', 'bank_mapping', 'manual', 'none'
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if confidence is high (>0.8)."""
        return self.confidence > 0.8
    
    @property
    def is_medium_confidence(self) -> bool:
        """Check if confidence is medium (0.5-0.8)."""
        return 0.5 <= self.confidence <= 0.8
    
    @property
    def needs_review(self) -> bool:
        """Check if this categorization needs human review."""
        return self.confidence < 0.5 or self.category is None
