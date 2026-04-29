# Transaction Categorizer

A local web application that extracts expense transactions from Deutsche Bank MHTML exports, categorizes them according to your budget structure, and outputs organized data ready for Google Sheets.

## What It Does

1. **Parse** — Reads your Deutsche Bank transaction export (.mhtml file)
2. **Categorize** — Automatically assigns transactions to budget categories (Food, Utilities, Income, etc.) using learned patterns
3. **Review** — Web interface to manually categorize transactions the system couldn't auto-detect
4. **Export** — Generates TSV format for easy copy-paste into Google Sheets

The system learns from your manual categorizations. After categorizing a merchant once (e.g., "ALDI" → Food/Groceries), future transactions from that merchant are automatically categorized.

## Quick Start

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python3 app.py

# Open browser
open http://127.0.0.1:5500
```

## Usage

1. **Upload** — Save your Deutsche Bank transactions page as `.mhtml` and upload it
2. **Review** — Check auto-categorized transactions, manually categorize any that need review
3. **Export** — Download TSV file or copy to clipboard, paste into Google Sheets

## Documentation

- **[PRD.md](PRD.md)** — Product requirements, user stories, budget categories
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Technical design, API endpoints, data flow
- **[AGENTS.md](AGENTS.md)** — Development guide for contributors

## Requirements

- Python 3.9+
- Works entirely offline — no data leaves your machine

## License

Personal use tool. All data stays local.
