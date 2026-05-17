"""Configuration settings for Transaction Categorizer."""

from typing import Dict, List, Optional

# Budget categories structure (from Budgeting 2026 PDF template)
BUDGET_CATEGORIES: Dict[str, List[str]] = {
    "Income": [
        "Job Salary",
        "Other Benefits"
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
        "Familiy's expenses"
    ],
    "Investments": [
        "Rurüp contribution (pension)",
        "Geiger Edelmetalle",
        "Scalable Capital Wealth",
        "BMI life insurance policy"
    ]
}

CATEGORY_MIGRATIONS: Dict[str, str] = {
    "Home Expenses/Cleaning Supplies": "Home Expenses/Decoration stuff/Cleaning Supplies",
    "Home Expenses/Rent": "Home Expenses/Rent (Germany)",
    "Other/Other Expenses (Cash/Debit)": "Other/Other expenses with cash/debit card",
    "Other/E-commerce": "Other/Expenses with credit card (TF Bank)",
    "Debt/Credit Card TF Bank": "Other/Expenses with credit card (TF Bank)",
    "Other/Bike/Scooter": "Other/Bike, scooter",
    "Other/Kids Countertop": "Other/Kids countertop",
    "Utilities/Cell Phones": "Utilities/Cell phones",
    "Utilities/TV Streaming / Cloud Storage": "Utilities/TV streaming / Cloud storage",
    "Utilities/Home Internet": "Utilities/Home internet",
    "Education/Fiorella's Expenses": "Education/Fiorella's expenses",
    "Education/Fernando's Expenses": "Education/Fernando's expenses",
    "Education/German Classes": "Education/German classes",
    "Education/TSVs / Extracurricular Activities": "Education/TSVs, extracurricular activities",
    "Transportation/General Maintenance": "Transportation/General maintenance",
    "Health/Family's Expenses": "Health/Familiy's expenses",
    "Investments/Rürup Contribution": "Investments/Rurüp contribution (pension)",
    "Investments/BMI Life Insurance": "Investments/BMI life insurance policy",
}


def normalize_budget_category(category: Optional[str]) -> Optional[str]:
    """Return the current template category for older stored/rule labels."""
    if category is None:
        return None
    return CATEGORY_MIGRATIONS.get(category, category)


# Default mappings from Deutsche Bank source categories to app budget categories.
# Source labels can vary by Deutsche Bank locale/export language.
DEFAULT_BANK_MAPPINGS: Dict[str, Optional[str]] = {
    "Lebensmittel / Getränke": "Food/Groceries",
    "Kleidung / Schuhe": "Other/Clothing",
    "Drogerieartikel": "Home Expenses/Decoration stuff/Cleaning Supplies",
    "Internetkäufe": "Other/Expenses with credit card (TF Bank)",
    "Öffentliche Verkehrsmittel": "Transportation/Bus",
    "Energie & Wasser": "Utilities/Electricity",
    "Telefon / Internet / Fernsehen / Radio": "Utilities/Cell phones",
    "Apotheke / Medikamente": "Health/Familiy's expenses",
    "Sport / Fitness": "Other/Entertainment",
    "Bücher / Musik / Filme / Apps": "Education/Fernando's expenses",
    "Lebensversicherung": "Investments/BMI life insurance policy",
    "Sonstige Ausgaben Versicherung": "Other/Insurances",
    "Miete / Nebenkosten": "Home Expenses/Rent (Germany)",
    "Lohn / Gehalt": "Income/Job Salary",
    "Sonstige Einnahmen": "Income/Other Benefits",
    "Kindergeld": "Income/Other Benefits",
    "Schulgeld": "Education/Fiorella's expenses",
    "Berufliche Weiterbildung": "Education/German classes",
    "Bargeld": "Other/Other expenses with cash/debit card",
    "Sonstiges": "Other/Other expenses with cash/debit card",
    "Motorrad": "Transportation/General maintenance",
    "Restaurants / Cafes / Bars": "Food/Dining Out",
    "Unkategorisiert": None,
    "Food / Beverages": "Food/Groceries",
    "Clothing / Shoes": "Other/Clothing",
    "Toiletries / Cleaning Supplies": "Home Expenses/Decoration stuff/Cleaning Supplies",
    "Online Shopping": "Other/Expenses with credit card (TF Bank)",
    "Public Transport": "Transportation/Bus",
    "Energy & water": "Utilities/Electricity",
    "Phone / Internet / TV / Radio": "Utilities/Cell phones",
    "Pharmacy / Drugs": "Health/Familiy's expenses",
    "Books / Music / Movies / Apps": "Education/Fernando's expenses",
    "Life Insurance": "Investments/BMI life insurance policy",
    "Life  Insurance": "Investments/BMI life insurance policy",
    "Other Editions Insurance": "Other/Insurances",
    "Rent / Associated Costs": "Home Expenses/Rent (Germany)",
    "Salary / Wages": "Income/Job Salary",
    "Other Income": "Income/Other Benefits",
    "Child Allowance": "Income/Other Benefits",
    "School Fees": "Education/Fiorella's expenses",
    "Professional Training": "Education/German classes",
    "Cash": "Other/Other expenses with cash/debit card",
    "Others": "Other/Other expenses with cash/debit card",
    "Uncategorized": None
}

# Paths for static categorization rules
PREFIX_RULES_PATH = 'config/prefix_rules.json'
CONTAINS_RULES_PATH = 'config/contains_rules.json'
EXPORT_TEMPLATE_PATH = 'config/export_template.tsv'

# Flask configuration
class Config:
    """Flask configuration."""
    SECRET_KEY = 'dev-key-change-in-production'
    UPLOAD_FOLDER = '/tmp/transaction_categorizer'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
    CONFIG_PATH = 'config/categorization_rules.json'
    DEBUG = True
