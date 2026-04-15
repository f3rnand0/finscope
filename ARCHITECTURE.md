# Transaction Categorizer - Architecture Document

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRANSACTION CATEGORIZER                            │
│                            (Local Web Application)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │  Web UI      │───▶│  API Layer   │───▶│  Core Engine │───▶│  Output   │ │
│  │  (Flask)     │    │  (REST)      │    │  (Python)    │    │  (TSV)    │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └───────────┘ │
│         │                   │                   │                           │
│         ▼                   ▼                   ▼                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  Templates   │    │  Services    │    │  Config File │                  │
│  │  (HTML/JS)   │    │  (Business   │    │  (JSON)      │                  │
│  │              │    │   Logic)     │    │              │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Core Technologies
| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.9+ |
| Web Framework | Flask | 2.3+ |
| HTML Parser | BeautifulSoup4 | 4.12+ |
| Data Processing | Pandas | 2.0+ |
| Frontend | Vanilla JS + Bootstrap 5 | 5.3+ |

### Dependencies
```
flask>=2.3.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
pytest>=7.4.0
pytest-cov>=4.1.0
```

**Note**: Pandas was removed from implementation - using standard library only.

## Directory Structure

```
transaction-categorizer/
├── app.py                    # Flask application entry point
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── config/                   # Configuration storage
│   └── categorization_rules.json
├── static/                   # Static web assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── templates/                # HTML templates
│   ├── base.html
│   ├── upload.html
│   ├── review.html
│   └── export.html
├── src/                      # Core modules
│   ├── __init__.py
│   ├── parser.py            # MHTML parsing
│   ├── categorizer.py       # Smart categorization engine
│   ├── models.py            # Data models
│   └── exporter.py          # Output generation
└── tests/                    # Unit tests
    ├── test_parser.py
    ├── test_categorizer.py
    └── test_exporter.py
```

## Core Components

### 1. Parser Module (src/parser.py)

**Purpose**: Extract transaction data from Deutsche Bank MHTML files

**Key Functions**:
```python
class MHTMLParser:
    def decode_content(self, content: bytes) -> str:
        # Decode quoted-printable MHTML content using quopri module
        
    def extract_transactions(self, content: bytes) -> List[Transaction]:
        # Parse MHTML and extract transaction records
        # Returns list of Transaction objects
        
    def parse_amount(self, amount_str: str) -> Decimal:
        # Parse standard number format with comma thousands separator
        # Example: '-8,000.00' -> Decimal('-8000.00')
        
    def parse_date(self, date_str: str) -> datetime:
        # Parse German date format (DD.MM.YYYY)
        
    def extract_merchant_from_description(self, description: str) -> str:
        # Extract merchant name from full transaction description
        # Handles location separators (//) and common suffixes
```

**Data Flow**:
1. Read binary MHTML file
2. Decode quoted-printable encoding
3. Parse HTML with BeautifulSoup
4. Extract transaction rows (<db-list-row> elements)
5. Parse individual fields (date, description, amount, category)
6. Return list of Transaction objects

### 2. Categorizer Module (src/categorizer.py)

**Purpose**: Smart transaction categorization with learning capability

**Key Classes**:
```python
class CategorizationEngine:
    def __init__(self, config_path: str):
        self.rules = self.load_rules(config_path)
        
    def categorize(self, transaction: Transaction) -> CategorizationResult:
        # Categorize a single transaction
        
    def learn_from_manual(self, transaction: Transaction, category: str):
        # Update patterns from manual categorization
        
    def extract_merchant(self, description: str) -> str:
        # Extract merchant name from description
        
    def calculate_confidence(self, pattern: str, category: str) -> float:
        # Calculate confidence score for a pattern match

class CategorizationRules:
    # Manages persistent categorization rules
    
    def add_merchant_rule(self, merchant: str, category: str)
    def add_keyword_rule(self, keyword: str, category: str)
    def get_category_for_merchant(self, merchant: str) -> Optional[str]
    def save_rules(self)
```

**Categorization Priority**:
1. Exact merchant match (highest confidence)
2. Partial merchant match
3. Keyword in description
4. Bank category mapping
5. Uncategorized (requires manual review)

### 3. Models Module (src/models.py)

**Data Classes**:
```python
@dataclass
class Transaction:
    id: str
    date: datetime
    counter_party: str
    description: str
    amount: Decimal
    bank_category: str
    budget_category: Optional[str] = None
    confidence: float = 0.0
    
    @property
    def is_expense(self) -> bool:  # True if amount < 0
    @property
    def is_income(self) -> bool:   # True if amount > 0
    @property
    def merchant(self) -> Optional[str]:  # Extracted from description
    def to_dict(self) -> dict:  # For JSON serialization

@dataclass
class CategorizationResult:
    category: Optional[str]
    confidence: float
    method: str  # 'merchant', 'keyword', 'bank_mapping', 'manual', 'none'
    
    @property
    def is_high_confidence(self) -> bool:     # > 0.8
    @property
    def is_medium_confidence(self) -> bool:   # 0.5 - 0.8
    @property
    def needs_review(self) -> bool:           # < 0.5 or no category
```

### 4. Exporter Module (src/exporter.py)

**Purpose**: Generate output in budget format

**Key Functions**:
```python
class BudgetExporter:
    def __init__(self, budget_template: Dict):
        self.template = budget_template
        
    def export_to_tsv(self, transactions: List[Transaction]) -> str:
        # Generate TSV string for Google Sheets
        
    def aggregate_by_category(self, transactions: List[Transaction]) -> Dict:
        # Group transactions by budget category
        
    def calculate_summary(self, categories: Dict) -> BudgetSummary:
        # Calculate totals and variances

class BudgetSummary:
    total_income: Decimal
    total_expenses: Decimal
    total_investments: Decimal
    uncategorized_count: int
```

## API Endpoints (Flask)

### Web Pages
```
GET /                    → Redirect to upload
GET /upload              → Upload page
GET /review              → Review & categorize transactions
GET /export              → Export preview and download
```

### API Endpoints
```
POST /api/upload
  - Accepts: multipart/form-data with MHTML file
  - Returns: {
      success: true,
      transaction_count: N,
      categorized_count: N,
      uncategorized_count: N,
      redirect: '/review'
    }

GET /api/transactions
  - Query params: category ('all', 'uncategorized'), search
  - Returns: { transactions: [Transaction, ...] }

POST /api/transactions/categorize
  - Body: { transaction_ids: ['tx_1', ...], category: 'Food/Groceries' }
  - Returns: { success: true, updated_count: N }
  - Side effect: Learns from manual categorization

POST /api/transactions/auto-categorize
  - Body: None
  - Returns: { success: true, categorized_count: N, total_count: N }

GET /api/export/tsv
  - Returns: TSV file download (budget_export.tsv)

GET /api/export/summary
  - Returns: {
      summary: {
        total_transactions: N,
        categorized_count: N,
        uncategorized_count: N,
        total_income: str,
        total_expenses: str,
        net: str
      }
    }
```

## Web Interface Pages

### 1. Upload Page (/upload)
**Template**: upload.html
- Drag-and-drop file zone
- File type validation (MHTML)
- Progress indicator
- Redirect to review page on success

### 2. Review Page (/review)
**Template**: review.html
- Data table with:
  - Sortable columns
  - Inline category dropdown
  - Bulk selection checkboxes
- Filter sidebar:
  - Uncategorized only toggle
  - Date range picker
  - Search box
- Action buttons:
  - "Auto-Categorize" (runs categorization engine)
  - "Save & Export"

### 3. Export Page (/export)
**Template**: export.html
- Preview table of final output
- Summary statistics cards
- Download buttons (TSV, CSV)
- Copy to clipboard button

## Configuration File Schema

```json
{
  "version": "1.0.0",
  "last_updated": "2024-03-15T10:30:00Z",
  "merchant_rules": {
    "ALDI": {
      "category": "Food/Groceries",
      "confidence": 0.95,
      "occurrence_count": 15
    },
    "AMAZON": {
      "category": "Other/E-commerce",
      "confidence": 0.85,
      "occurrence_count": 8
    }
  },
  "keyword_rules": {
    "TELEKOM": {
      "category": "Utilities/Cell Phones",
      "confidence": 0.95
    },
    "SCALABLE": {
      "category": "Investments/Scalable Capital",
      "confidence": 0.98
    }
  },
  "bank_category_mappings": {
    "Food / Beverages": "Food/Groceries",
    "Clothing / Shoes": "Other/Clothing",
    "Online Shopping": "Other/E-commerce",
    "Public Transport": "Transportation/Bus",
    "Energy & water": "Utilities/Electricity",
    "Phone / Internet / TV / Radio": "Utilities/Cell Phones",
    "Life Insurance": "Investments/BMI Life Insurance",
    "Other Income": "Income/Other Benefits",
    "Salary / Wages": "Income/Job Salary"
  },
  "manual_rules": [
    {
      "pattern": "Rürüp",
      "category": "Investments/Rürup Contribution"
    }
  ]
}
```

## Data Flow

### Upload Flow
```
1. User uploads MHTML file via /api/upload
   ↓
2. Flask receives file (stored in memory, not saved to disk)
   ↓
3. MHTMLParser.decode_content() → decode quoted-printable
   ↓
4. MHTMLParser.extract_transactions() → parse HTML, extract rows
   ↓
5. Transaction objects created (78 transactions in test file)
   ↓
6. CategorizationEngine.auto_categorize_all() → apply rules
   ↓
7. Results stored in Flask session as JSON
   ↓
8. Return summary, redirect to /review
```

### Categorization Flow
```
1. User selects transaction(s) + assigns category via dropdown
   ↓
2. POST /api/transactions/categorize
   ↓
3. Update transaction(s) budget_category in session
   ↓
4. CategorizationEngine.learn_from_manual()
   ↓
5. Extract merchant from description
   ↓
6. CategorizationRules.add_merchant_rule() → update JSON
   ↓
7. Save to config/categorization_rules.json
   ↓
8. Return success, update UI
```

### Export Flow
```
1. User clicks "Download TSV" on /export page
   ↓
2. GET /api/export/tsv
   ↓
3. Load transactions from session, convert to Transaction objects
   ↓
4. BudgetExporter.aggregate_by_category()
   ↓
5. BudgetExporter.export_to_tsv() → generate TSV string
   ↓
6. Return as file download (budget_export.tsv)
```

## Error Handling

### Parser Errors
- **Invalid file format**: Return 400 with clear message
- **Encoding issues**: Try multiple encodings, log warnings
- **Missing fields**: Mark as "incomplete", still show in UI

### Categorization Errors
- **No patterns match**: Leave as "Uncategorized"
- **Low confidence**: Flag for review (yellow highlight)
- **Conflicting patterns**: Use highest confidence, log warning

### Config Errors
- **Corrupted config**: Backup and create new
- **Missing config**: Create default
- **Permission denied**: Show error, use in-memory only

## Security Considerations

1. **File Upload**: Validate file type, size limit (10MB)
2. **Path Traversal**: Use secure temp directories only
3. **XSS Prevention**: Jinja2 auto-escaping in templates
4. **CSRF Protection**: Flask-WTF for forms
5. **Local Only**: Bind to 127.0.0.1 by default

## Testing Strategy

### Unit Tests (28 tests, all passing)
```bash
pytest tests/                    # Run all tests
pytest tests/test_parser.py -v  # Parser tests
pytest tests/test_categorizer.py -v  # Categorizer tests
pytest tests/test_exporter.py -v  # Exporter tests
pytest --cov=src tests/         # With coverage
```

### Test Coverage
- **Parser**: Date/amount parsing, HTML entity cleaning, merchant extraction
- **Categorizer**: Rule loading/saving, merchant matching, keyword matching, learning
- **Exporter**: Category aggregation, TSV generation, summary calculation

### Test Data
- Tests use actual MHTML file format from Deutsche Bank
- Mock transactions for edge cases (incomplete data, special characters)

## Deployment

### Local Development
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Access
- URL: http://127.0.0.1:5000
- Debug mode: Enabled for development

## Future Architecture Considerations

1. **Database**: SQLite for transaction history
2. **Multi-user**: User authentication for shared installs
3. **API**: RESTful API for mobile apps
4. **Sync**: Cloud sync of categorization rules
