# Finscope Context

Finscope is a local web application for turning Deutsche Bank MHTML transaction exports into categorized budget data that can be reviewed in a browser and exported to Google Sheets.

## Product Purpose

The app helps a single user parse monthly bank transactions, categorize them against a household budget structure, learn recurring merchant patterns, and export a TSV summary without sending financial data to any external service.

## Domain Terms

- **Transaction**: A single bank movement parsed from a Deutsche Bank MHTML export. It includes a date, counter party, description, amount, bank category, optional budget category, and confidence score.
- **Bank category**: Deutsche Bank's source category label for a transaction. Source labels can vary by export locale and are used only as mapping inputs.
- **Budget category**: The English household budget category assigned by this app, such as `Food/Groceries`, `Utilities/Cell Phones`, or `Investments/Geiger Edelmetalle`.
- **Categorization rule**: A persisted JSON rule used to assign future transactions to budget categories.
- **Merchant rule**: A categorization rule keyed by an extracted merchant name, such as `ALDI`, and used before keyword or bank-category fallback logic.
- **Keyword rule**: A categorization rule keyed by a meaningful word or phrase found in a transaction description.
- **Export**: The TSV output intended for Google Sheets, including category, subcategory, description, actual spend, and transaction counts.

## Core Flow

1. The user uploads a Deutsche Bank `.mhtml` export.
2. The parser decodes quoted-printable MHTML and extracts `<db-list-row>` transaction data.
3. The categorizer assigns budget categories using merchant rules, partial merchant matches, keyword rules, bank category mappings, then uncategorized fallback.
4. The user reviews and manually categorizes remaining transactions.
5. Manual choices update local categorization rules for future imports.
6. The exporter generates TSV budget output for Google Sheets.

## Invariants

- Financial data processing and categorization must stay on the user's machine.
- Frontend assets may load from CDN; do not send transaction data to external services.
- Use `Decimal` for money values; do not use floats for amounts.
- German date input uses `DD.MM.YYYY`.
- Deutsche Bank amount strings use German money format: dot thousands separators and comma decimals, such as `-8.000,00`.
- Invalid amount text must fail upload with row context instead of silently importing as zero.
- Bank category names are source labels only; map them into English budget categories before display/export behavior depends on them.
- App UI, exports, templates, and budget categories remain in English.
- Flask routes should stay thin and delegate parsing, categorization, and export behavior to `src/` modules.

## Supporting References

- `PRD.md` defines product requirements, user stories, budget categories, and expected output format.
- `ARCHITECTURE.md` describes the Flask app, core modules, routes, and data flow.
- `AGENTS.md` contains contributor guidance, quick-start commands, code patterns, and gotchas.
