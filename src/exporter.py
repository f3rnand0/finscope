"""Export transactions to budget format (TSV)."""

import csv
import io
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Dict, List

from .models import Transaction
from config import BUDGET_CATEGORIES, EXPORT_TEMPLATE_PATH, normalize_budget_category


class BudgetExporter:
    """Export transactions to budget format."""

    EXPORT_COLUMNS = ['Category / Expense', 'Budget', 'Actual Spent', 'Budget vs. Actual']
    
    def __init__(self, template_path: str = EXPORT_TEMPLATE_PATH):
        self.category_hierarchy = self._build_category_hierarchy()
        self.template_path = Path(template_path)
    
    def _build_category_hierarchy(self) -> Dict[str, List[str]]:
        """Build flat category to subcategory mapping."""
        hierarchy = {}
        for main_cat, subcats in BUDGET_CATEGORIES.items():
            for subcat in subcats:
                key = f"{main_cat}/{subcat}"
                hierarchy[key] = [main_cat, subcat]
        return hierarchy
    
    def aggregate_by_category(self, transactions: List[Transaction]) -> Dict[str, dict]:
        """Group transactions by budget category, excluding excluded transactions."""
        categories = defaultdict(lambda: {
            'transactions': [],
            'total': Decimal('0'),
            'count': 0
        })

        for tx in transactions:
            if tx.excluded:
                continue
            category = normalize_budget_category(tx.budget_category) or 'Uncategorized/Uncategorized'
            categories[category]['transactions'].append(tx)
            categories[category]['total'] += tx.amount
            categories[category]['count'] += 1

        return dict(categories)
    
    def _format_description(self, transactions: List[Transaction]) -> str:
        """Format descriptions as Merchant Title##Description per transaction."""
        lines = []
        for tx in transactions:
            merchant = tx.counter_party or ''
            desc = tx.description or ''
            lines.append(f"{merchant}##{desc}")
        return '\n'.join(lines)

    def export_to_tsv(self, transactions: List[Transaction]) -> str:
        """Generate template-shaped TSV string for Google Sheets."""
        aggregated = self.aggregate_by_category(transactions)
        rows = self._render_template_rows(aggregated)

        output = io.StringIO()
        writer = csv.writer(output, delimiter='\t', lineterminator='\n')
        writer.writerows(rows)

        return output.getvalue()

    def _load_spending_template(self) -> List[dict]:
        """Load template rows from the spending table header onward."""
        with self.template_path.open(newline='', encoding='utf-8') as f:
            rows = list(csv.reader(f, delimiter='\t'))

        header_index = next(
            (
                index for index, row in enumerate(rows)
                if row and row[0].strip() == 'Category / Expense'
            ),
            None
        )
        if header_index is None:
            raise ValueError('Export template is missing the Category / Expense header')

        headers = rows[header_index]
        column_indexes = {name: headers.index(name) for name in self.EXPORT_COLUMNS}
        template_rows = []

        for row in rows[header_index:]:
            padded = row + [''] * (len(headers) - len(row))
            template_rows.append({
                name: padded[index]
                for name, index in column_indexes.items()
            })

        return template_rows

    def _render_template_rows(self, aggregated: Dict[str, dict]) -> List[List[str]]:
        rows = []
        current_category = None
        subcategory_rows = []

        for row in self._load_spending_template():
            label = row['Category / Expense'].strip()

            if label == 'Category / Expense':
                rows.append(self.EXPORT_COLUMNS)
                continue

            if not label:
                rows.append(['', '', '', ''])
                continue

            if label.startswith('TOTAL SPENDING'):
                actual = self._total_actual(subcategory_rows, aggregated, label)
                budget = row['Budget']
                rows.append([
                    label,
                    budget,
                    self._format_currency(actual) if actual != 0 else '',
                    self._format_variance(self._parse_currency(budget) - actual)
                ])
                continue

            if label.startswith('- '):
                subcategory = label[2:]
                category_key = f"{current_category}/{subcategory}"
                subcategory_rows.append(category_key)
                data = aggregated.get(category_key, {'total': Decimal('0'), 'count': 0})
                actual = abs(data['total'])
                has_transactions = data['count'] > 0
                rows.append([
                    row['Category / Expense'],
                    row['Budget'],
                    self._format_currency(actual) if has_transactions else '',
                    self._format_variance(self._parse_currency(row['Budget']) - actual)
                ])
                continue

            current_category = label
            rows.append([label, row['Budget'], '', ''])

        return rows

    def _total_actual(self, category_keys: List[str], aggregated: Dict[str, dict], label: str) -> Decimal:
        total = Decimal('0')
        for category_key in category_keys:
            if label == 'TOTAL SPENDING WITHOUT INVESTMENTS' and category_key.startswith('Investments/'):
                continue
            total += abs(aggregated.get(category_key, {'total': Decimal('0')})['total'])
        return total

    def _parse_currency(self, value: str) -> Decimal:
        value = value.strip()
        if not value:
            return Decimal('0')
        return Decimal(value.replace('€', '').replace(',', '').strip())

    def _format_currency(self, amount: Decimal) -> str:
        return f"€{amount:,.2f}"

    def _format_variance(self, amount: Decimal) -> str:
        if amount == 0:
            return ''
        return self._format_currency(amount)
    
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
                if ',' in f or '"' in f or '\n' in f:
                    escaped = f.replace('"', '""')
                    quoted_fields.append(f'"{escaped}"')
                else:
                    quoted_fields.append(f)
            csv_lines.append(','.join(quoted_fields))
        return '\n'.join(csv_lines)
    
    def get_summary(self, transactions: List[Transaction]) -> dict:
        """Get summary statistics, excluding excluded transactions."""
        active = [tx for tx in transactions if not tx.excluded]
        total_income = sum(tx.amount for tx in active if tx.is_income)
        total_expenses = sum(tx.amount for tx in active if tx.is_expense)
        uncategorized_count = sum(1 for tx in active if not tx.budget_category)
        categorized_count = len(active) - uncategorized_count

        return {
            'total_transactions': len(active),
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
            if tx.excluded:
                continue
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
