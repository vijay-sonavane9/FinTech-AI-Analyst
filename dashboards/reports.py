# Generate monthly/weekly reports
# dashboards/reports.py
import pandas as pd
from agents.summarizer import summarize_period
from agents.advisor import advice_text

def make_report(df: pd.DataFrame, title: str, budgets: dict) -> str:
    s = summarize_period(df, title=title)
    a = advice_text(df, budgets)
    return f"{s}\n\n{a}"
