# Categorizer Agent
# agents/categorizer.py
import re
import pandas as pd

CATEGORY_RULES = {
    "Food": ["swiggy","zomato","restaurant","cafe","eatfit","food","domino","pizza","kfc","mcd"],
    "Transport": ["uber","ola","rapido","fuel","petrol","diesel","metro","bus","train","cab","toll"],
    "Shopping": ["amazon","flipkart","myntra","ajio","shop","store","decathlon"],
    "Housing": ["rent","security deposit","landlord","society"],
    "Utilities": ["electricity","water","gas","internet","wifi","broadband","mobile","recharge","dth"],
    "Entertainment": ["netflix","prime video","spotify","movie","bookmyshow","gaming"],
    "Health": ["pharmacy","medicine","apollo","lab","hospital","clinic"],
    "Education": ["udemy","coursera","course","exam","college","school","byjus"],
    "Travel": ["air","indigo","vistara","goair","train","irctc","hotel","booking.com","makemytrip","yatra","oyo"],
    "Groceries": ["bigbasket","jiomart","grofer","dmart","grocery","milk","vegetable","fruit"],
    "Subscriptions": ["subscription","renewal","membership","license"],
    "Transfers": ["transfer","upi to","imps","neft","rtgs","paytm wallet","to self","wallet"],
    "Income": ["salary","stipend","refund","cashback","reversal","interest"],
    "Others": []
}

def _classify_desc(text: str) -> str:
    s = str(text).lower()
    for cat, keywords in CATEGORY_RULES.items():
        for k in keywords:
            if k in s:
                return cat
    return "Others"

def categorize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    # incomes: if income > expense mark as Income
    d["category"] = d["description"].map(_classify_desc)
    # If it's clearly income by value, override
    is_income = d["income"].fillna(0) > d["expense"].fillna(0)
    d.loc[is_income, "category"] = "Income"
    return d
