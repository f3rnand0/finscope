"""Configuration settings for Transaction Categorizer."""

from typing import Dict, List

# Budget categories structure (from March Budget PDF)
BUDGET_CATEGORIES: Dict[str, List[str]] = {
    "Income": [
        "Job salary",
        "Other benefits"
    ],
    "Home Expenses": [
        "Furniture/Repairs",
        "Cleaning Supplies",
        "Rent (Germany)"
    ],
    "Food": [
        "Groceries",
        "Dining Out"
    ],
    "Other": [
        "Clothing",
        "Other expenses with cash/debit card",
        "E-commerce",
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
    "Debt": [
        "Credit Card TF Bank"
    ],
    "Investments": [
        "Rurüp contribution (pension)",
        "Scalable Capital Wealth",
        "BMI life insurance policy"
    ]
}

# Default mappings from Deutsche Bank categories to budget categories
DEFAULT_BANK_MAPPINGS: Dict[str, str] = {
    "Food / Beverages": "Food/Groceries",
    "Clothing / Shoes": "Other/Clothing",
    "Toiletries / Cleaning Supplies": "Home Expenses/Cleaning Supplies",
    "Online Shopping": "Other/E-commerce",
    "Public Transport": "Transportation/Bus",
    "Energy & water": "Utilities/Electricity",
    "Phone / Internet / TV / Radio": "Utilities/Cell phones",
    "Pharmacy / Drugs": "Health/Family's expenses",
    "Sport / Fitness": "Other/Entertainment",
    "Books / Music / Movies / Apps": "Education/Fernando's expenses",
    "Life Insurance": "Investments/BMI life insurance policy",
    "Other Editions Insurance": "Other/Insurances",
    "Rent / Associated Costs": "Home Expenses/Rent (Germany)",
    "Salary / Wages": "Income/Job salary",
    "Other Income": "Income/Other benefits",
    "Child Allowance": "Income/Other benefits",
    "School Fees": "Education/Fiorella's expenses",
    "Professional Training": "Education/German classes",
    "Cash": "Other/Other expenses with cash/debit card",
    "Others": "Other/Other expenses with cash/debit card",
    "Uncategorized": None
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
