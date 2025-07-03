# app.py  ───────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd

#---------- 1. load data --------------------------------------------
@st.cache_data  # caches after first load; speeds up reruns
def load_data():
    return pd.read_csv(
        "data/fraud_dataset_full.csv",
        parse_dates=["transaction_date_time"]      # keep timestamp column as datetime
    )

df = load_data()

#---------- 2. basic page setup -------------------------------------
st.set_page_config(page_title="Fraud Trend Analysis Challenge",
                   page_icon="🕵️",
                   layout="wide")

st.title("🕵️‍♂️ Fraud Trend Analysis – 60-Minute Challenge")
st.markdown(
"""
**Your tasks (complete in 60 min):**

1. Explore the data using the filters and charts below.  
2. Identify 2-3 emerging fraud trends (channels, countries, merchants, velocity spikes, etc.).  
3. Recommend 2-3 strategic control actions.  
4. Enter your insights in the text box at the bottom *or* send them separately (max 300 words).
"""
)

#---------- 3. sidebar filters --------------------------------------
st.sidebar.header("🔍 Quick filters")

# date range
date_min = df["transaction_date_time"].dt.date.min()
date_max = df["transaction_date_time"].dt.date.max()
start_date, end_date = st.sidebar.date_input(
    "Date range",
    (date_min, date_max),
)

# transaction type
txn_types = sorted(df["transaction_type_desc"].unique())
chosen_txn = st.sidebar.multiselect("Transaction type", txn_types)

# country
countries = sorted(df["merchant_country_code"].unique())
chosen_cty = st.sidebar.multiselect("Merchant country", countries)

# apply filters
mask = (
    (df["transaction_date_time"].dt.date.between(start_date, end_date))
    & (df["transaction_type_desc"].isin(chosen_txn) if chosen_txn else True)
    & (df["merchant_country_code"].isin(chosen_cty) if chosen_cty else True)
)
view = df[mask]

st.write(f"**{len(view):,} transactions** match your filters.")

#---------- 4. quick charts -----------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Daily fraud rate (%)")
    daily = (
        view.groupby(view["transaction_date_time"].dt.date)["fraud"]
        .mean()
        .mul(100)
        .rename("fraud_rate")
    )
    st.line_chart(daily)

with col2:
    st.subheader("🗺️ Fraud rate by country (%)")
    by_country = (
        view.groupby("merchant_country_code")["fraud"]
        .mean()
        .mul(100)
        .sort_values(ascending=False)
        .head(15)
    )
    st.bar_chart(by_country)

#---------- 5. raw data preview -------------------------------------
st.subheader("Raw data (first 2 000 rows)")
st.dataframe(view.head(2000), height=300)

#---------- 6. candidate input box ----------------------------------
insights = st.text_area(
    "✍️ Paste your key insights & recommended controls here (optional)",
    placeholder="e.g. Contactless fraud spiked 40 % last two weeks; consider lowering limits…",
    height=150,
)
