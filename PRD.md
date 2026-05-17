# Transaction Categorizer - Product Requirements Document (PRD)

## Overview
A local web application that extracts expense transactions from Deutsche Bank MHTML files, categorizes them according to a budget structure, and outputs organized data ready for Google Sheets import.

## Goals
1. Parse transaction data from Deutsche Bank MHTML export files
2. Automatically categorize transactions based on learned patterns
3. Provide a web interface for manual review and categorization
4. Output data in a budget format matching the March Budget structure
5. Remember categorization rules for future transactions

## User Stories

### Story 1: Initial Setup
As a user, I want to upload my MHTML transaction file and see all transactions extracted with their details (date, description, amount, existing category).

### Story 2: Manual Categorization
As a user, I want to review uncategorized transactions and assign them to budget categories, so the system learns my categorization patterns.

### Story 3: Automatic Categorization
As a user, I want the system to automatically categorize future transactions based on patterns learned from my previous categorizations (merchant name, description keywords).

### Story 4: Budget Output
As a user, I want to export the categorized transactions in a format that matches my budget structure, ready to copy-paste into Google Sheets.

### Story 5: Persistent Rules
As a user, I want my categorization rules to be saved locally, so I don't have to recategorize the same merchants every month.

## Functional Requirements

### FR1: MHTML Parsing
- Parse Deutsche Bank MHTML format
- Extract: Date, Counter Party, Description, Amount, Existing Category
- Handle quoted-printable encoding
- Support single file upload

### FR2: Category Mapping
- Map bank categories to budget categories
- Support custom category mappings
- Allow multiple bank categories to map to one budget category

### FR3: Smart Categorization
- Extract merchant/company names from transaction descriptions
- Store keyword patterns for each budget category
- Auto-categorize based on learned patterns
- Confidence scoring for auto-categorizations

### FR4: Web Interface
- Upload page: Drag-and-drop MHTML file upload
- Review page: Table view of all transactions
- Categorization panel: Dropdown to assign categories to selected transactions
- Filter options: Show only Uncategorized, search by description
- Export page: Preview output format, download TSV

### FR5: Configuration Persistence
- Save categorization rules to local JSON file
- Store: merchant patterns, keyword patterns, category mappings
- Load rules on application start
- Manual rule editing capability

### FR6: Output Format
- Generate tab-separated values (TSV) format
- Structure matching March Budget PDF:
  - Main Category
  - Subcategory
  - Actual Spent (sum of transactions)
  - Description
- Include transaction count per category
- Monthly summary totals

## Non-Functional Requirements

### NFR1: Local Data Processing
- Run categorization and export processing on the local machine
- Do not send transaction data to external APIs or cloud storage
- Frontend assets may load from CDN

### NFR2: Performance
- Parse 1000+ transactions in under 5 seconds
- Web UI responsive with 500+ transactions

### NFR3: Data Privacy
- All data stays on local machine
- No network calls for categorization

### NFR4: Portability
- Configuration file is human-readable JSON
- Easy backup and migration of categorization rules

## Budget Categories (from March Budget)

### Income
- Job Salary
- Other Benefits

### Home Expenses
- Furniture/Repairs
- Cleaning Supplies
- Rent

### Food
- Groceries
- Dining Out

### Other
- Clothing
- Other Expenses (Cash/Debit)
- E-commerce
- Entertainment
- Bike/Scooter
- Charity
- Insurances
- Kids Countertop

### Utilities
- Electricity
- Cell Phones
- ARD ZDF Radio
- TV Streaming / Cloud Storage
- Home Internet

### Education
- Fiorella's Expenses
- Fernando's Expenses
- German Classes
- TSVs / Extracurricular Activities

### Transportation
- Bus
- General Maintenance

### Health
- Family's Expenses

### Debt
- Credit Card TF Bank

### Investments
- Rürup Contribution
- Geiger Edelmetalle
- Scalable Capital Wealth
- BMI Life Insurance

## Input Data Format

### MHTML Source Fields
- **Date**: DD.MM.YYYY format
- **Counter Party**: Transaction type label (e.g., "Debit Card Payment")
- **Description**: Full transaction details with merchant, location, date/time
- **Amount**: Positive (income) or negative (expense) EUR values in German money format, such as `500,00` or `5.089,71`
- **Bank Category**: Pre-assigned category from Deutsche Bank

### Bank Categories to Map
Deutsche Bank source labels can vary by export locale. They are mapping inputs only; the app-facing budget categories remain English.

Observed English source labels include:
- Food / Beverages
- Clothing / Shoes
- Toiletries / Cleaning Supplies
- Online Shopping
- Public Transport
- Energy & water
- Phone / Internet / TV / Radio
- Pharmacy / Drugs
- Sport / Fitness
- Books / Music / Movies / Apps
- Life Insurance
- Other Editions Insurance
- Rent / Associated Costs
- Salary / Wages
- Other Income
- Child Allowance
- School Fees
- Professional Training
- Cash
- Others
- Uncategorized

German source labels such as `Lebensmittel / Getränke`, `Miete / Nebenkosten`, and `Lohn / Gehalt` are also supported where mappings exist.

## Output Data Format

### TSV Structure for Google Sheets
```
Category	Subcategory	Actual Spent	Description	Transaction Count
Income	Job Salary	€5,089.71	Employer##Monthly salary	1
Income	Other Benefits	€518.00	Tax office##Tax compensation	1
Home Expenses	Rent	€1,970.00	Landlord##Rent	1
Food	Groceries	€520.45	ALDI##ALDI SE U. CO. KG//Muenchen/DE	12
```

## User Interface Requirements

### Page 1: Upload
- Title: "Transaction Categorizer"
- File drop zone for MHTML files
- Upload button
- Progress indicator
- Error messages for invalid files

### Page 2: Review & Categorize
- Summary cards: Total transactions, Uncategorized count, Total income, Total expenses
- Data table columns:
  - Income table: Date, Merchant Title, Detailed Description, Amount
  - Expenses table: Checkbox, Budget Category, Merchant Title, Detailed Description, Amount, Date, Actions
  - Excluded expenses table: Merchant Title, Detailed Description, Amount, Date, Actions
- Filters:
  - Show only Uncategorized
  - Search by description
- Bulk action: Select multiple rows, assign category to all
- "Learn Patterns" button: Train on manually categorized transactions

### Page 3: Export
- Preview of output format
- Download TSV button
- Copy to clipboard button
- Summary statistics

## Smart Categorization Algorithm (Implemented)

### Pattern Learning (Active)
When user assigns a category via the web interface:
1. Extract merchant name from transaction description (e.g., "ALDI" from "ALDI SE U. CO. KG//Muenchen/DE")
2. Store in `config/categorization_rules.json`:
   - Merchant rule: {"ALDI": {"category": "Food/Groceries", "confidence": 0.8, "count": 1}}
3. On subsequent matches, confidence increases (max 0.95)

### Auto-categorization Priority (Implemented)
1. **Exact learned merchant match** → Confidence 0.8-0.95 (based on count)
2. **Partial learned merchant match** → Confidence × 0.8 (e.g., "ALDI SE" matches "ALDI")
3. **Learned keyword match** → Confidence 0.6 (significant words from description)
4. **Static prefix rule** → Confidence 0.95
5. **Static contains rule** → Confidence 0.90
6. **Bank category mapping** → Confidence 0.5 (fallback)
7. **Uncategorized** → Requires manual review

### Confidence Thresholds
- **High (>0.8)**: Auto-accepted, shown with green background
- **Medium (0.5-0.8)**: Auto-suggested, user can confirm
- **Low (<0.5)**: Left as "Uncategorized", requires manual assignment

### Tested Results
With fresh install (no learned patterns), categorization uses static rules and bank
category mappings. After manual categorization of recurring merchants, learned rules
increase coverage over time.

### Configuration File Structure
```json
{
  "version": "1.0",
  "patterns": {
    "merchants": {
      "ALDI": {"category": "Food/Groceries", "confidence": 0.95, "count": 12},
      "AMAZON": {"category": "Other/E-commerce", "confidence": 0.88, "count": 8}
    },
    "keywords": {
      "REWE": {"category": "Food/Groceries", "confidence": 0.90},
      "TELEKOM": {"category": "Utilities/Cell Phones", "confidence": 0.95}
    }
  },
  "bank_category_mappings": {
    "Food / Beverages": "Food/Groceries",
    "Lebensmittel / Getränke": "Food/Groceries",
    "Online Shopping": "Other/E-commerce"
  },
  "manual_rules": [
    {"pattern": "Scalable Capital", "category": "Investments/Scalable Capital Wealth"}
  ]
}
```

## Success Criteria (Achieved)

| Criterion | Target | Achieved | Notes |
|-----------|--------|----------|-------|
| Parse transactions | 100% | ✅ 71/71 | Test MHTML has 78 source rows: 6 settlement rows skipped, 1 duplicate deduplicated |
| Auto-categorization | >70% | Tracked by tests | Static mappings provide baseline coverage; learned rules improve with use |
| Google Sheets import | Clean | ✅ TSV | Tab-separated format tested and working |
| Web UI responsive | Yes | ✅ | Bootstrap 5, works on laptop/tablet |
| Config persistence | Yes | ✅ | JSON file at `config/categorization_rules.json` |
| All tests passing | 100% | Tracked by pytest | Unit and e2e tests cover parser, categorizer, exporter, and Flask routes |

### Performance Metrics
- **Parse speed**: ~71 transactions/second on the fixture
- **Categorization**: Instant (in-memory rules)
- **Export**: <100ms for the fixture transaction set
- **Session handling**: Uses a server-side in-memory transaction store keyed by a small Flask session id

## Future Enhancements (Out of Scope)
- Multi-currency support
- Multiple bank format support
- Historical trend analysis
- Budget variance alerts
- Cloud sync of categorization rules
