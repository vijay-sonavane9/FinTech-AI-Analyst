# Summarizer Agent
# agents/summarizer.py
import pandas as pd

def summarize_period(df: pd.DataFrame, title: str = "Summary") -> str:
    if df.empty:
        return f"{title}: No transactions in the selected period."

    total_exp = df["amount"].sum()
    by_cat = df.groupby("category")["amount"].sum().sort_values(ascending=False)
    top_line = f"{title}: Total spend ₹{total_exp:,.0f}."

    bullets = []
    for cat, val in by_cat.head(5).items():
        if val <= 0: 
            continue
        bullets.append(f"- {cat}: ₹{val:,.0f}")

    if not bullets:
        bullets = ["- No expenses detected (only income or zero amounts)."]

    return "\n".join([top_line, *bullets])
