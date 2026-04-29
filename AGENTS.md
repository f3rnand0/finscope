# AGENTS.md - Transaction Categorizer

Practical guidance for this codebase.

## Quick Start

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py  # http://127.0.0.1:5500
```

## Key Patterns

### Parser (src/parser.py)
MHTML is quoted-printable encoded:
```python
import quopri
decoded = quopri.decodestring(raw_bytes).decode('utf-8')
```

German formats:
- Dates: `DD.MM.YYYY` → `datetime.strptime(d, '%d.%m.%Y')`
- Amounts: Standard format with comma as thousands separator (e.g., `-8,000.00`) → `Decimal(s.replace(',', ''))`

### Categorizer (src/categorizer.py)
Priority: exact merchant match → partial match → keyword → bank category → uncategorized

### Flask Routes (app.py)
Keep thin - delegate to src/ modules.

## Common Tasks

### Add Budget Category
1. Add to `BUDGET_CATEGORIES` in config.py
2. Add mapping in `DEFAULT_BANK_MAPPINGS`
3. Update templates/review.html

### Fix MHTML Parsing
Check structure with `quopri.decodestring()`, look for `<db-list-row>` elements.

## Testing

```bash
pytest tests/                    # All tests
pytest tests/test_parser.py -v  # Specific
pytest --cov=src tests/         # Coverage
```

## Debugging

```python
# Test merchant extraction
from src.categorizer import CategorizationEngine
e = CategorizationEngine(':memory:')
print(e.extract_merchant('ALDI SE U. CO. KG//Muenchen/DE'))

# Check config
import json
with open('config/categorization_rules.json') as f:
    print(json.dumps(json.load(f), indent=2))
```

## Gotchas

1. **Session size**: Flask sessions are cookie-based. Don't store all transactions there for large files.
2. **Decimal**: Always use `Decimal`, never float for amounts.
3. **Merchant names**: Vary between "ALDI" and "ALDI SE U. CO. KG" - use regex, not exact match.
4. **HTML entities**: Bank categories have `&amp;` - decode them.

## Code Style

- Python: PEP 8, type hints
- JavaScript: camelCase
- HTML: Bootstrap 5

## Security

- Validate file uploads (MHTML only, 10MB max)
- Use Jinja2 auto-escaping (enabled by default)
- Bind to 127.0.0.1 (local only)
