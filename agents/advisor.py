# Advisor Agent
# agents/advisor.py
import pandas as pd
from typing import Dict, List, Tuple

def overspend_report(df: pd.DataFrame, budgets: Dict[str, float]) -> List[Tuple[str, float, float, float]]:
    """
    Returns list of (category, actual, budget, pct_over) where actual > budget.
    """
    if df.empty:
        return []
    by_cat = df.groupby("category")["amount"].sum()
    rows = []
    for cat, actual in by_cat.items():
        b = budgets.get(cat, None)
        if b and actual > b:
            pct = ((actual - b) / b) * 100.0
            rows.append((cat, actual, b, pct))
    rows.sort(key=lambda x: x[3], reverse=True)
    return rows

def advice_text(df: pd.DataFrame, budgets: Dict[str, float]) -> str:
    overs = overspend_report(df, budgets)
    if not overs:
        return "Good job! You are within budget for all categories in this period."
    lines = ["Overspending detected:"]
    for cat, actual, budget, pct in overs:
        lines.append(f"- {cat}: spent ₹{actual:,.0f} vs budget ₹{budget:,.0f} (**{pct:.0f}% over**)")
    return "\n".join(lines)
