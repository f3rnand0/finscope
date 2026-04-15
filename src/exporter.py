"""Export transactions to budget format (TSV)."""

import io
from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Tuple

from .models import Transaction
from config import BUDGET_CATEGORIES


class BudgetExporter:
    """Export transactions to budget format."""
    
    def __init__(self):
        self.category_hierarchy = self._build_category_hierarchy()
    
    def _build_category_hierarchy(self) -> Dict[str, List[str]]:
        """Build flat category to subcategory mapping."""
        hierarchy = {}
        for main_cat, subcats in BUDGET_CATEGORIES.items():
            for subcat in subcats:
                key = f"{main_cat}/{subcat}"
                hierarchy[key] = [main_cat, subcat]
        return hierarchy
    
    def aggregate_by_category(self, transactions: List[Transaction]) -> Dict[str, dict]:
        """Group transactions by budget category."""
        categories = defaultdict(lambda: {
            'transactions': [],
            'total': Decimal('0'),
            'count': 0
        })
        
        for tx in transactions:
            category = tx.budget_category or 'Uncategorized/Uncategorized'
            categories[category]['transactions'].append(tx)
            categories[category]['total'] += tx.amount
            categories[category]['count'] += 1
        
        return dict(categories)
    
    def export_to_tsv(self, transactions: List[Transaction]) -> str:
        """Generate TSV string for Google Sheets."""
        aggregated = self.aggregate_by_category(transactions)
        
        rows = []
        
        # Header row
        rows.append(['Category', 'Subcategory', 'Description', 'Budget', 'Actual Spent', 'Variance', 'Transaction Count'])
        
        # Income first
        for main_cat in ['Income']:
            if main_cat in BUDGET_CATEGORIES:
                for subcat in BUDGET_CATEGORIES[main_cat]:
                    cat_key = f"{main_cat}/{subcat}"
                    data = aggregated.get(cat_key, {'total': Decimal('0'), 'count': 0, 'transactions': []})
                    
                    # Get description from transactions
                    descriptions = [tx.description[:40] for tx in data['transactions'][:3]]
                    desc = ', '.join(descriptions) if descriptions else ''
                    
                    rows.append([
                        main_cat,
                        subcat,
                        desc,
                        '',  # Budget - user fills manually
                        f"€{abs(data['total']):,.2f}" if data['total'] != 0 else '',
                        '',  # Variance - calculated in sheet
                        str(data['count'])
                    ])
        
        # Expenses (all other categories)
        for main_cat in BUDGET_CATEGORIES:
            if main_cat == 'Income':
                continue
                
            for subcat in BUDGET_CATEGORIES[main_cat]:
                cat_key = f"{main_cat}/{subcat}"
                data = aggregated.get(cat_key, {'total': Decimal('0'), 'count': 0, 'transactions': []})
                
                # Skip empty categories unless they have transactions
                if data['count'] == 0:
                    continue
                
                # Get description from transactions
                descriptions = [tx.description[:40] for tx in data['transactions'][:3]]
                desc = ', '.join(descriptions) if descriptions else ''
                
                rows.append([
                    main_cat,
                    subcat,
                    desc,
                    '',  # Budget - user fills manually
                    f"€{abs(data['total']):,.2f}",
                    '',  # Variance - calculated in sheet
                    str(data['count'])
                ])
        
        # Uncategorized transactions
        uncategorized = aggregated.get('Uncategorized/Uncategorized', {'total': Decimal('0'), 'count': 0, 'transactions': []})
        if uncategorized['count'] > 0:
            descriptions = [tx.description[:40] for tx in uncategorized['transactions'][:3]]
            desc = ', '.join(descriptions) if descriptions else ''
            rows.append([
                'Uncategorized',
                'Needs Review',
                desc,
                '',
                f"€{abs(uncategorized['total']):,.2f}",
                '',
                str(uncategorized['count'])
            ])
        
        # Convert to TSV
        output = io.StringIO()
        for row in rows:
            output.write('\t'.join(row) + '\n')
        
        return output.getvalue()
    
    def export_to_csv(self, transactions: List[Transaction]) -> str:
        """Generate CSV string."""
        tsv = self.export_to_tsv(transactions)
        # Replace tabs with commas, handle quoting
        lines = tsv.strip().split('\n')
        csv_lines = []
        for line in lines:
            fields = line.split('\t')
            quoted_fields = []
            for f in fields:
                if ',' in f or '"' in f:
                    escaped = f.replace('"', '""')
                    quoted_fields.append(f'"{escaped}"')
                else:
                    quoted_fields.append(f)
            csv_lines.append(','.join(quoted_fields))
        return '\n'.join(csv_lines)
    
    def get_summary(self, transactions: List[Transaction]) -> dict:
        """Get summary statistics."""
        total_income = sum(tx.amount for tx in transactions if tx.is_income)
        total_expenses = sum(tx.amount for tx in transactions if tx.is_expense)
        uncategorized_count = sum(1 for tx in transactions if not tx.budget_category)
        categorized_count = len(transactions) - uncategorized_count
        
        return {
            'total_transactions': len(transactions),
            'categorized_count': categorized_count,
            'uncategorized_count': uncategorized_count,
            'total_income': total_income,
            'total_expenses': abs(total_expenses),
            'net': total_income + total_expenses
        }
    
    def export_transactions_list(self, transactions: List[Transaction]) -> str:
        """Export raw transactions as TSV for detailed view."""
        rows = []
        rows.append(['Date', 'Description', 'Amount', 'Bank Category', 'Budget Category', 'Confidence'])
        
        for tx in transactions:
            rows.append([
                tx.date.strftime('%d.%m.%Y') if tx.date else '',
                tx.description[:60],
                f"€{tx.amount:,.2f}",
                tx.bank_category,
                tx.budget_category or 'Uncategorized',
                f"{tx.confidence:.0%}" if tx.confidence > 0 else ''
            ])
        
        output = io.StringIO()
        for row in rows:
            output.write('\t'.join(row) + '\n')
        
        return output.getvalue()
