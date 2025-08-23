# CSV Preprocessing Functions
# utils/preprocess.py
from __future__ import annotations
import re
from typing import Optional, Tuple, List
import pandas as pd
import numpy as np
from dateutil import tz
from config.settings import TIMEZONE, BASE_CURRENCY, USD_TO_INR_RATE

DATE_CANDIDATES = [
    "Date","Transaction Date","Posting Date","Txn Date","Value Date"
]
DESC_CANDIDATES = [
    "Description","Details","Narration","Merchant","Remarks",
    "Transaction Description","Particulars","Info"
]
AMOUNT_CANDIDATES = [
    "Amount","Amt","Txn Amount","Transaction Amount","Value","AMOUNT"
]
DEBIT_CANDIDATES  = ["Debit","Withdrawal","DR","Debited"]
CREDIT_CANDIDATES = ["Credit","Deposit","CR","Credited"]

def _find_col(cols: List[str], candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in cols:
            return c
    # try case-insensitive match
    lower = {c.lower(): c for c in cols}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None

def _strip_currency_and_parse(x: str) -> Tuple[Optional[float], Optional[str]]:
    """Return (number, currency) if possible."""
    if pd.isna(x):
        return None, None
    s = str(x).strip()
    currency = None
    if "₹" in s or "INR" in s.upper():
        currency = "INR"
    elif "$" in s or "USD" in s.upper():
        currency = "USD"
    # keep digits, - and .
    cleaned = re.sub(r"[^0-9\.\-]", "", s)
    if cleaned in ("", "-", ".", "-.", ".-"):
        return None, currency
    try:
        return float(cleaned), currency
    except ValueError:
        return None, currency

def _ensure_datetime(series: pd.Series) -> pd.Series:
    # try dayfirst=True (common in India), fallback to False
    s = pd.to_datetime(series, errors="coerce", dayfirst=True, infer_datetime_format=True)
    if s.isna().all():
        s = pd.to_datetime(series, errors="coerce", dayfirst=False, infer_datetime_format=True)
    # localize to timezone (naive -> tz-aware)
    try:
        s = s.dt.tz_localize(TIMEZONE, nonexistent="NaT", ambiguous="NaT")
    except Exception:
        # if already tz-aware or error, just convert
        try:
            s = s.dt.tz_convert(TIMEZONE)
        except Exception:
            pass
    return s

def _standardize_amounts(df: pd.DataFrame, original_amount_col: Optional[str]) -> pd.DataFrame:
    df = df.copy()
    if original_amount_col:
        nums, currs = zip(*df[original_amount_col].map(_strip_currency_and_parse))
        df["_amount_raw"] = pd.Series(nums, index=df.index)
        df["_currency_hint"] = pd.Series(currs, index=df.index)
    else:
        df["_amount_raw"] = np.nan
        df["_currency_hint"] = None

    # If separate Debit/Credit exist, compute from them
    debit_col  = _find_col(list(df.columns), DEBIT_CANDIDATES)
    credit_col = _find_col(list(df.columns), CREDIT_CANDIDATES)
    if debit_col or credit_col:
        # Parse debit/credit values
        if debit_col:
            df["_debit"], _ = zip(*df[debit_col].map(_strip_currency_and_parse))
        else:
            df["_debit"] =  [0.0]*len(df)
        if credit_col:
            df["_credit"], _ = zip(*df[credit_col].map(_strip_currency_and_parse))
        else:
            df["_credit"] = [0.0]*len(df)
        # Expenses = positive, Income = positive
        df["expense"] = pd.to_numeric(df["_debit"]).fillna(0.0)
        df["income"]  = pd.to_numeric(df["_credit"]).fillna(0.0)
    else:
        # Single Amount column -> assume positive = expense by default
        amt = pd.to_numeric(df["_amount_raw"], errors="coerce").fillna(0.0)
        # Heuristic: if there's a 'Type' column with 'debit/credit', respect it
        type_col = _find_col(list(df.columns), ["Type","Transaction Type","Dr/Cr"])
        if type_col:
            t = df[type_col].astype(str).str.lower()
            df["expense"] = np.where(t.str.contains("cr") | t.str.contains("credit"), 0.0, np.abs(amt))
            df["income"]  = np.where(t.str.contains("cr") | t.str.contains("credit"), np.abs(amt), 0.0)
        else:
            # Default: treat positive as expense
            df["expense"] = np.where(amt >= 0, amt, 0.0)
            df["income"]  = np.where(amt < 0,  -amt, 0.0)

    # Currency column if present
    currency_col = _find_col(list(df.columns), ["Currency","Curr"])
    if currency_col:
        df["currency"] = df[currency_col].astype(str).str.upper().str.replace("₹","INR").str.replace("$","USD")
    else:
        # Use hint else base currency
        df["currency"] = df["_currency_hint"].fillna(BASE_CURRENCY)

    # Convert USD->INR for both expense & income (simple fallback)
    is_usd = df["currency"].eq("USD")
    df.loc[is_usd, "expense"] = df.loc[is_usd, "expense"] * USD_TO_INR_RATE
    df.loc[is_usd, "income"]  = df.loc[is_usd, "income"]  * USD_TO_INR_RATE
    df["currency"] = BASE_CURRENCY

    # Final unified 'amount' for expenses analysis
    df["amount"] = df["expense"].astype(float)

    return df

def load_and_clean(input_obj) -> pd.DataFrame:
    """
    input_obj: path-like, file-like (Streamlit UploadedFile), or DataFrame
    Returns standardized DataFrame with columns:
    ['date','description','amount','expense','income','currency'] (+ originals preserved)
    """
    if isinstance(input_obj, pd.DataFrame):
        raw = input_obj.copy()
    else:
        raw = pd.read_csv(input_obj)

    cols = list(raw.columns)
    date_col = _find_col(cols, DATE_CANDIDATES)
    desc_col = _find_col(cols, DESC_CANDIDATES)
    amount_col = _find_col(cols, AMOUNT_CANDIDATES)

    if date_col is None:
        raise ValueError("Could not detect a Date column. Rename one column to 'Date'.")
    if desc_col is None:
        # If no description-like column, create one
        raw["__Description"] = ""
        desc_col = "__Description"

    df = raw.copy()
    df["date"] = _ensure_datetime(df[date_col])
    df["description"] = df[desc_col].astype(str)

    df = _standardize_amounts(df, amount_col)
    df = df.dropna(subset=["date"])  # drop rows with invalid dates
    df = df.sort_values("date").reset_index(drop=True)
    return df[["date","description","amount","expense","income","currency"] + [c for c in raw.columns if c not in ("date","description")]]
