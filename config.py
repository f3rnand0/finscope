"""Configuration settings for Transaction Categorizer."""

from typing import Dict, List

# Budget categories structure (from March Budget PDF)
BUDGET_CATEGORIES: Dict[str, List[str]] = {
    "Income": [
        "Job Salary",
        "Other Benefits"
    ],
    "Home Expenses": [
        "Furniture/Repairs",
        "Cleaning Supplies",
        "Rent"
    ],
    "Food": [
        "Groceries",
        "Dining Out"
    ],
    "Other": [
        "Clothing",
        "Other Expenses (Cash/Debit)",
        "E-commerce",
        "Entertainment",
        "Bike/Scooter",
        "Charity",
        "Insurances",
        "Kids Countertop"
    ],
    "Utilities": [
        "Electricity",
        "Cell Phones",
        "ARD ZDF Radio",
        "TV Streaming / Cloud Storage",
        "Home Internet"
    ],
    "Education": [
        "Fiorella's Expenses",
        "Fernando's Expenses",
        "German Classes",
        "TSVs / Extracurricular Activities"
    ],
    "Transportation": [
        "Bus",
        "General Maintenance"
    ],
    "Health": [
        "Family's Expenses"
    ],
    "Debt": [
        "Credit Card TF Bank"
    ],
    "Investments": [
        "Rürup Contribution",
        "Scalable Capital Wealth",
        "BMI Life Insurance"
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
    "Phone / Internet / TV / Radio": "Utilities/Cell Phones",
    "Pharmacy / Drugs": "Health/Family's Expenses",
    "Sport / Fitness": "Other/Entertainment",
    "Books / Music / Movies / Apps": "Education/Fernando's Expenses",
    "Life Insurance": "Investments/BMI Life Insurance",
    "Other Editions Insurance": "Other/Insurances",
    "Rent / Associated Costs": "Home Expenses/Rent",
    "Salary / Wages": "Income/Job Salary",
    "Other Income": "Income/Other Benefits",
    "Child Allowance": "Income/Other Benefits",
    "School Fees": "Education/Fiorella's Expenses",
    "Professional Training": "Education/German Classes",
    "Cash": "Other/Other Expenses (Cash/Debit)",
    "Others": "Other/Other Expenses (Cash/Debit)",
    "Uncategorized": None
}

# Flask configuration
class Config:
    """Flask configuration."""
    SECRET_KEY = 'dev-key-change-in-production'
    UPLOAD_FOLDER = '/tmp/transaction_categorizer'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
    CONFIG_PATH = 'config/categorization_rules.json'
    DEBUG = True
