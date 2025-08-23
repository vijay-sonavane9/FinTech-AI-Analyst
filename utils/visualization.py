# Chart/Plot Functions
# utils/visualization.py
import pandas as pd
import plotly.express as px

def pie_by_category(df: pd.DataFrame):
    d = df.copy()
    if "category" not in d.columns or "amount" not in d.columns:
        return None
    d = d.groupby("category", as_index=False)["amount"].sum()
    d = d[d["amount"] > 0]
    if d.empty:
        return None
    return px.pie(d, names="category", values="amount", title="Spending by Category")


def trend_by_date(df: pd.DataFrame):
    d = df.copy()
    if "date" not in d.columns or "amount" not in d.columns:
        return None

    # Ensure datetime and build a proper day column for grouping
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    # If tz-aware, drop tz to keep a clean daily index; then normalize to midnight
    try:
        if d["date"].dt.tz is not None:
            d["day"] = d["date"].dt.tz_convert(None).dt.normalize()
        else:
            d["day"] = d["date"].dt.normalize()
    except Exception:
        d["day"] = pd.to_datetime(d["date"], errors="coerce").dt.normalize()

    d = d.dropna(subset=["day"])
    d["amount"] = pd.to_numeric(d["amount"], errors="coerce").fillna(0.0)
    d = d.groupby("day", as_index=False)["amount"].sum()

    if d.empty:
        return None
    return px.line(d, x="day", y="amount", title="Daily Spending Trend")


def bar_top_categories(df: pd.DataFrame, top_n: int = 5, title="Top Categories"):
    d = df.copy()
    if "category" not in d.columns or "amount" not in d.columns:
        return None
    d["amount"] = pd.to_numeric(d["amount"], errors="coerce").fillna(0.0)
    d = d.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
    d = d[d["amount"] > 0].head(top_n)
    if d.empty:
        return None
    return px.bar(d, x="category", y="amount", title=title)
