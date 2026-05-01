"""Configuration settings for Transaction Categorizer."""

from typing import Dict, List

# Budget categories structure (from Budgeting 2026 PDF template)
BUDGET_CATEGORIES: Dict[str, List[str]] = {
    "Income": [
        "Job salary",
        "Other benefits"
    ],
    "Home Expenses": [
        "Furniture/Repairs",
        "Decoration stuff/Cleaning Supplies",
        "Rent (Germany)"
    ],
    "Food": [
        "Groceries",
        "Dining Out"
    ],
    "Other": [
        "Clothing",
        "Other expenses with cash/debit card",
        "Expenses with credit card (TF Bank)",
        "Entertainment",
        "Bike, scooter",
        "Charity",
        "Insurances",
        "Kids countertop"
    ],
    "Utilities": [
        "Electricity",
        "Cell phones",
        "ARD ZDF Radio",
        "TV streaming / Cloud storage",
        "Home internet"
    ],
    "Education": [
        "Fiorella's expenses",
        "Fernando's expenses",
        "German classes",
        "TSVs, extracurricular activities"
    ],
    "Transportation": [
        "Bus",
        "General maintenance"
    ],
    "Health": [
        "Family's expenses"
    ],
    "Investments": [
        "Rurüp contribution (pension)",
        "Geiger Edelmetale",
        "Scalable Capital Wealth",
        "BMI life insurance policy"
    ]
}

# Default mappings from Deutsche Bank categories (German) to budget categories
DEFAULT_BANK_MAPPINGS: Dict[str, str] = {
    "Lebensmittel / Getränke": "Food/Groceries",
    "Kleidung / Schuhe": "Other/Clothing",
    "Drogerieartikel": "Home Expenses/Decoration stuff/Cleaning Supplies",
    "Internetkäufe": "Other/Expenses with credit card (TF Bank)",
    "Öffentliche Verkehrsmittel": "Transportation/Bus",
    "Energie & Wasser": "Utilities/Electricity",
    "Telefon / Internet / Fernsehen / Radio": "Utilities/Cell phones",
    "Sport / Fitness": "Other/Entertainment",
    "Bücher / Musik / Filme / Apps": "Education/Fernando's expenses",
    "Lebensversicherung": "Investments/BMI life insurance policy",
    "Sonstige Ausgaben Versicherung": "Other/Insurances",
    "Miete / Nebenkosten": "Home Expenses/Rent (Germany)",
    "Lohn / Gehalt": "Income/Job salary",
    "Sonstige Einnahmen": "Income/Other benefits",
    "Kindergeld": "Income/Other benefits",
    "Schulgeld": "Education/Fiorella's expenses",
    "Bargeld": "Other/Other expenses with cash/debit card",
    "Sonstiges": "Other/Other expenses with cash/debit card",
    "Motorrad": "Transportation/General maintenance",
    "Restaurants / Cafes / Bars": "Food/Dining Out",
    "Unkategorisiert": None
}

# Paths for static categorization rules
PREFIX_RULES_PATH = 'config/prefix_rules.json'
CONTAINS_RULES_PATH = 'config/contains_rules.json'

# Flask configuration
class Config:
    """Flask configuration."""
    SECRET_KEY = 'dev-key-change-in-production'
    UPLOAD_FOLDER = '/tmp/transaction_categorizer'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
    CONFIG_PATH = 'config/categorization_rules.json'
    DEBUG = True
