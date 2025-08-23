# # Chatbot Agent
# # agents/chatbot.py
# import re
# import pandas as pd
# from datetime import timedelta
# from typing import Tuple, Optional
# from config.settings import TIMEZONE
# from utils.visualization import bar_top_categories
# import pytz

# def _now():
#     return pd.Timestamp.now(tz=TIMEZONE)

# def _period_from_text(text: str, df: pd.DataFrame) -> Tuple[pd.Timestamp, pd.Timestamp, str]:
#     text = text.lower()
#     now = _now()
#     # default: this month
#     start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
#     end   = now

#     label = "this month"

#     if "last week" in text:
#         end   = now
#         start = end - timedelta(days=7)
#         label = "last week"
#     elif "this week" in text:
#         weekday = now.weekday()  # Monday=0
#         start = (now - pd.Timedelta(days=weekday)).normalize()
#         end = now
#         label = "this week"
#     elif "last month" in text:
#         first_this_month = now.replace(day=1)
#         end = first_this_month - pd.Timedelta(seconds=1)
#         start = (first_this_month - pd.offsets.MonthBegin(1)).tz_convert(TIMEZONE)
#         label = "last month"
#     elif "this month" in text:
#         start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
#         end = now
#         label = "this month"
#     elif "all time" in text or "overall" in text:
#         start = df["date"].min()
#         end = df["date"].max()
#         label = "overall"

#     return start, end, label

# def _filter_period(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
#     return df[(df["date"] >= start) & (df["date"] <= end)]

# def _total_spent(d: pd.DataFrame) -> float:
#     return d["amount"].sum()

# def _top_category(d: pd.DataFrame) -> Optional[Tuple[str, float]]:
#     g = d.groupby("category")["amount"].sum().sort_values(ascending=False)
#     g = g[g > 0]
#     if g.empty:
#         return None
#     cat = g.index[0]
#     val = g.iloc[0]
#     return cat, float(val)

# def _extract_top_n(text: str, default: int = 5) -> int:
#     m = re.search(r"top\s+(\d+)", text.lower())
#     if m:
#         return max(1, int(m.group(1)))
#     return default

# def answer_question(df: pd.DataFrame, question: str, budgets: dict) -> Tuple[str, Optional[object]]:
#     """
#     Returns (answer_text, plotly_fig or None)
#     """
#     if df.empty:
#         return "No data available. Please upload a CSV first.", None

#     q = question.strip()
#     start, end, label = _period_from_text(q, df)
#     d = _filter_period(df, start, end)

#     if d.empty:
#         return f"No transactions found for {label}.", None

#     ql = q.lower()

#     # Overspend question
#     if "overspend" in ql or "over spend" in ql or "exceed" in ql or "over budget" in ql:
#         # Compare spend vs budget
#         from agents.advisor import overspend_report
#         rows = overspend_report(d, budgets)
#         if not rows:
#             return f"No overspending detected {label}. 🎉", None
#         # Build a bar chart for those categories
#         odf = pd.DataFrame(rows, columns=["category","actual","budget","pct_over"])
#         text = f"Overspending {label}:\n" + "\n".join(
#             [f"- {r.category}: ₹{r.actual:,.0f} (budget ₹{r.budget:,.0f}) — {r.pct_over:.0f}% over"
#              for r in odf.itertuples()]
#         )
#         fig = bar_top_categories(d[d["category"].isin(odf["category"])], top_n=len(odf), title="Overspent Categories")
#         return text, fig

#     # Total spent
#     if "total" in ql and ("spent" in ql or "spend" in ql or "expense" in ql):
#         total = _total_spent(d)
#         return f"Total spent {label}: ₹{total:,.0f}.", None

#     # Top categories
#     if "top" in ql and "categor" in ql:
#         n = _extract_top_n(ql, default=5)
#         fig = bar_top_categories(d, top_n=n, title=f"Top {n} Categories ({label})")
#         cat = _top_category(d)
#         if cat:
#             return f"Top {n} categories {label} shown below. Biggest: {cat[0]} (₹{cat[1]:,.0f}).", fig
#         else:
#             return f"No expenses {label}.", None

#     # Fallback: brief stats
#     cat = _top_category(d)
#     total = _total_spent(d)
#     if cat:
#         return f"{label.title()} — Total spent ₹{total:,.0f}. Biggest category: {cat[0]} (₹{cat[1]:,.0f}).", None
#     return f"{label.title()} — Total spent ₹{total:,.0f}.", None


# Chatbot Agent
# agents/chatbot.py
import re
import pandas as pd
from datetime import timedelta
from typing import Tuple, Optional
from config.settings import TIMEZONE
from utils.visualization import bar_top_categories
import pytz

def _now():
    return pd.Timestamp.now(tz=TIMEZONE)

def _period_from_text(text: str, df: pd.DataFrame) -> Tuple[pd.Timestamp, pd.Timestamp, str]:
    text = text.lower()
    now = _now()
    # default: this month
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end   = now

    label = "this month"

    if "last week" in text:
        end   = now
        start = end - timedelta(days=7)
        label = "last week"
    elif "this week" in text:
        weekday = now.weekday()  # Monday=0
        start = (now - pd.Timedelta(days=weekday)).normalize()
        end = now
        label = "this week"
    elif "last month" in text:
        first_this_month = now.replace(day=1)
        end = first_this_month - pd.Timedelta(seconds=1)
        start = (first_this_month - pd.offsets.MonthBegin(1)).tz_convert(TIMEZONE)
        label = "last month"
    elif "this month" in text:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
        label = "this month"
    elif "all time" in text or "overall" in text:
        start = df["date"].min()
        end = df["date"].max()
        label = "overall"

    return start, end, label

def _filter_period(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df[(df["date"] >= start) & (df["date"] <= end)]

def _total_spent(d: pd.DataFrame) -> float:
    return d["amount"].sum()

def _top_category(d: pd.DataFrame) -> Optional[Tuple[str, float]]:
    g = d.groupby("category")["amount"].sum().sort_values(ascending=False)
    g = g[g > 0]
    if g.empty:
        return None
    cat = g.index[0]
    val = g.iloc[0]
    return cat, float(val)

def _extract_top_n(text: str, default: int = 5) -> int:
    m = re.search(r"top\s+(\d+)", text.lower())
    if m:
        return max(1, int(m.group(1)))
    return default

def answer_question(df: pd.DataFrame, question: str, budgets: dict, monthly_income: float) -> Tuple[str, Optional[object]]:
    """
    Returns (answer_text, plotly_fig or None)
    """
    if df.empty:
        return "No data available. Please upload a CSV first.", None

    q = question.strip()
    start, end, label = _period_from_text(q, df)
    d = _filter_period(df, start, end)

    if d.empty:
        return f"No transactions found for {label}.", None

    ql = q.lower()

    # Remaining balance queries
    if "remaining" in ql or "balance" in ql or "left" in ql or "saving" in ql:
        total = _total_spent(d)
        remaining = monthly_income - total
        return f"Your remaining balance {label}: ₹{remaining:,.0f} (Income ₹{monthly_income:,.0f} - Spent ₹{total:,.0f}).", None

    # Overspend question
    if "overspend" in ql or "over spend" in ql or "exceed" in ql or "over budget" in ql:
        from agents.advisor import overspend_report
        rows = overspend_report(d, budgets)
        if not rows:
            return f"No overspending detected {label}. 🎉", None
        odf = pd.DataFrame(rows, columns=["category","actual","budget","pct_over"])
        text = f"Overspending {label}:\n" + "\n".join(
            [f"- {r.category}: ₹{r.actual:,.0f} (budget ₹{r.budget:,.0f}) — {r.pct_over:.0f}% over"
             for r in odf.itertuples()]
        )
        fig = bar_top_categories(d[d["category"].isin(odf["category"])], top_n=len(odf), title="Overspent Categories")
        return text, fig

    # Total spent
    if "total" in ql and ("spent" in ql or "spend" in ql or "expense" in ql):
        total = _total_spent(d)
        return f"Total spent {label}: ₹{total:,.0f}.", None

    # Top categories
    if "top" in ql and "categor" in ql:
        n = _extract_top_n(ql, default=5)
        fig = bar_top_categories(d, top_n=n, title=f"Top {n} Categories ({label})")
        cat = _top_category(d)
        if cat:
            return f"Top {n} categories {label} shown below. Biggest: {cat[0]} (₹{cat[1]:,.0f}).", fig
        else:
            return f"No expenses {label}.", None

    # Fallback: brief stats
    cat = _top_category(d)
    total = _total_spent(d)
    if cat:
        return f"{label.title()} — Total spent ₹{total:,.0f}. Biggest category: {cat[0]} (₹{cat[1]:,.0f}).", None
    return f"{label.title()} — Total spent ₹{total:,.0f}.", None
