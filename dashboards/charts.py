# Reusable chart functions
# dashboards/charts.py
import pandas as pd
from utils.visualization import pie_by_category, trend_by_date, bar_top_categories

def make_core_charts(df: pd.DataFrame):
    return {
        "pie": pie_by_category(df),
        "trend": trend_by_date(df),
        "top": bar_top_categories(df, top_n=5),
    }
