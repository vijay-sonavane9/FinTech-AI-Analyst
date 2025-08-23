import streamlit as st
import pandas as pd
from config.settings import APP_NAME, DEFAULT_BUDGETS, TIMEZONE
from utils.preprocess import load_and_clean
from utils.file_handler import save_uploaded_file, load_file
from agents.categorizer import categorize_transactions
from dashboards.charts import make_core_charts
from dashboards.reports import make_report
from agents.chatbot import answer_question

st.set_page_config(page_title=APP_NAME, page_icon="💰", layout="wide")

# --- State ---
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()
if "budgets" not in st.session_state:
    st.session_state.budgets = DEFAULT_BUDGETS.copy()
if "manual_data" not in st.session_state:
    st.session_state.manual_data = []

# --- Sidebar ---
st.sidebar.title("⚙️ Controls")

# File upload
uploaded = st.sidebar.file_uploader("Upload transactions CSV", type=["csv"])
if uploaded:
    path = save_uploaded_file(uploaded)
    try:
        df = load_file(path)  # Use our CSV loader
        df = load_and_clean(df)
        df = categorize_transactions(df)

        # Ensure timezone-aware
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if df["date"].dt.tz is None:
            df["date"] = df["date"].dt.tz_localize(
                TIMEZONE, nonexistent="shift_forward", ambiguous="NaT"
            )
        else:
            df["date"] = df["date"].dt.tz_convert(TIMEZONE)

        st.session_state.df = df
        st.sidebar.success("File processed successfully!")
    except Exception as e:
        st.sidebar.error(f"Failed to process CSV: {e}")

# Manual entry form
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Add Transaction Manually")
with st.sidebar.form("manual_entry_form", clear_on_submit=True):
    date = st.date_input("Date")
    description = st.text_input("Description")
    category = st.selectbox("Category", list(DEFAULT_BUDGETS.keys()))
    amount = st.number_input("Amount (INR)", min_value=0.0, format="%.2f")
    submitted = st.form_submit_button("Add")

if submitted:
    st.session_state.manual_data.append({
        "date": pd.Timestamp(date).tz_localize(TIMEZONE),
        "description": description,
        "category": category,
        "amount": amount,
        "currency": "INR",
    })
    st.sidebar.success("Transaction added!")

# Budgets
st.sidebar.markdown("---")
st.sidebar.subheader("Budgets (Monthly, INR)")
for k in list(st.session_state.budgets.keys()):
    st.session_state.budgets[k] = st.sidebar.number_input(
        k, value=float(st.session_state.budgets[k]), min_value=0.0, step=500.0
    )

# --- Monthly Income ---
st.sidebar.markdown("---")
st.sidebar.subheader("💵 Total Balance")
monthly_income = st.sidebar.number_input(
    "Enter your Total Balance (INR):", min_value=0, value=0, step=1000
)

# --- Main Content ---
st.title("💰 Personal Finance AI Dashboard")

# Merge data (CSV + manual)
df_csv = st.session_state.df.copy()
df_manual = pd.DataFrame(st.session_state.manual_data)

# Drop duplicate columns if any
df_csv = df_csv.loc[:, ~df_csv.columns.duplicated()]
df_manual = df_manual.loc[:, ~df_manual.columns.duplicated()]

# Ensure schema consistency
required_cols = ["date", "description", "category", "amount", "currency"]
for col in required_cols:
    if col not in df_csv.columns:
        df_csv[col] = None
    if col not in df_manual.columns:
        df_manual[col] = None

# Concatenate safely
df = pd.concat([df_csv[required_cols], df_manual[required_cols]], ignore_index=True)

# Ensure 'date' is datetime with timezone
df["date"] = pd.to_datetime(df["date"], errors="coerce")
if df["date"].notna().any():
    if df["date"].dt.tz is None:
        df["date"] = df["date"].dt.tz_localize(
            TIMEZONE, nonexistent="shift_forward", ambiguous="NaT"
        )
    else:
        df["date"] = df["date"].dt.tz_convert(TIMEZONE)



# Ensure numeric amounts
df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)

if df.empty:
    st.info("Upload a CSV or add manual transactions to get started.")
    st.stop()

# --- Period filter ---
col1, col2 = st.columns(2)
with col1:
    start = st.date_input(
        "Start date", value=pd.to_datetime(df["date"].min()).date()
    )
with col2:
    end = st.date_input(
        "End date", value=pd.to_datetime(df["date"].max()).date()
    )

start_ts = pd.Timestamp(start).tz_localize(TIMEZONE)
end_ts = pd.Timestamp(end).tz_localize(TIMEZONE) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

mask = (df["date"] >= start_ts) & (df["date"] <= end_ts)
view = df.loc[mask].copy()

if view.empty:
    st.warning("No transactions in this date range.")
    st.stop()

# --- KPIs ---
k1, k2 = st.columns(2)
total_spent = view["amount"].sum()
# days = (end_ts - start_ts).days + 1
remaining = monthly_income - total_spent

with k1:
    st.metric("Total Spent", f"₹{total_spent:,.0f}")
# with k2:
#     st.metric("Days", f"{days}")
with k2:
    st.metric("Remaining Balance", f"₹{remaining:,.0f}")

# --- Charts ---
charts = make_core_charts(view)
c1, c2 = st.columns([1, 1])
with c1:
    if charts.get("pie"):
        st.plotly_chart(charts["pie"], use_container_width=True)
    if charts.get("top"):
        st.plotly_chart(charts["top"], use_container_width=True)
with c2:
    if charts.get("trend"):
        st.plotly_chart(charts["trend"], use_container_width=True)

# --- Report ---
st.markdown("### 📜 AI Report")
st.text(make_report(view, title="Selected Period", budgets=st.session_state.budgets))

# --- Chatbot ---
st.markdown("---")
st.subheader("🤖 Data Q&A Chatbot")
q = st.text_input("Ask about your data (e.g., 'Where did I overspend last week?' or 'Top 3 categories this month')")
if st.button("Ask") and q.strip():
    ans, fig = answer_question(view, q, st.session_state.budgets, monthly_income)
    st.write(ans)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

# --- Table + Download ---
st.markdown("---")
st.subheader("📄 Processed Transactions")
st.dataframe(
    view[["date", "description", "category", "amount", "currency"]],
    use_container_width=True,
)

@st.cache_data
def to_csv(d: pd.DataFrame) -> bytes:
    return d.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download processed CSV",
    data=to_csv(view),
    file_name="processed_transactions.csv",
    mime="text/csv",
)
