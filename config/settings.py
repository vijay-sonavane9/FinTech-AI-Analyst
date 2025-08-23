# Configuration settings

# config/settings.py

# --- General ---
APP_NAME = "Personal Finance AI Dashboard"
TIMEZONE = "Asia/Kolkata"

# --- Currency ---
BASE_CURRENCY = "INR"
USD_TO_INR_RATE = 83.0  # fallback constant (update if you like)

# --- Default monthly budgets (INR) ---
DEFAULT_BUDGETS = {
    "Food": 6000,
    "Transport": 2500,
    "Shopping": 4000,
    "Housing": 10000,
    "Utilities": 3000,
    "Entertainment": 2000,
    "Health": 2000,
    "Education": 2000,
    "Travel": 5000,
    "Groceries": 6000,
    "Subscriptions": 1500,
    "Others": 3000,
}
