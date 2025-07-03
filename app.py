# app.py  – Fraud Trend Analysis Challenge
import streamlit as st
import pandas as pd

# ---------- 1. Load data -------------------------------------------------
@st.cache_data
def load_data():
    return pd.read_csv(
        "data/fraud_dataset_full_final.csv",      # <-- adjust if your CSV name differs
        parse_dates=["transaction_date_time"]
    )

df = load_data()

# ---------- 2. Basic page setup -----------------------------------------
st.set_page_config(
    page_title="Fraud Trend Analysis Challenge",
    page_icon="🕵️",
    layout="wide",
)
st.title("🕵️‍♂️ Fraud Trend Analysis – 60-Minute Challenge")
st.markdown(
"""
**Your tasks (60 min)**  

1. Use the filters and charts to explore the data.  
2. Identify **2–3 emerging fraud trends** (MCCs, POS modes, merchants, countries, velocity spikes, etc.).  
3. Recommend **2–3 strategic control actions**.  
4. Enter your insights in the text box below *or* send them separately (≤ 300 words).
"""
)

# ---------- 3. Sidebar filters (updated) --------------------------------
st.sidebar.header("🔍 Quick filters")

# Date range
date_min = df["transaction_date_time"].dt.date.min()
date_max = df["transaction_date_time"].dt.date.max()
start_date, end_date = st.sidebar.date_input(
    "Date range", (date_min, date_max)
)

# Merchant Category Code
mcc_options = sorted(df["merchant_category_code"].dropna().unique())
mcc_selected = st.sidebar.multiselect("Merchant category code (MCC)", mcc_options)

# POS Entry Mode (description)
pos_options = sorted(df["pos_entry_desc"].dropna().unique())
pos_selected = st.sidebar.multiselect("POS entry mode", pos_options)

# Merchant Name
mn_options = sorted(df["merchant_name"].dropna().unique())
mn_selected = st.sidebar.multiselect("Merchant names", mn_options)

# Fraud Type  – drop NaN and empty strings
ft_options = sorted([ft for ft in df["fraud_type"].dropna().unique() if ft])
ft_selected = st.sidebar.multiselect("Fraud types", ft_options)

# Merchant Country Code
cty_options = sorted(df["merchant_country_code"].dropna().unique())
cty_selected = st.sidebar.multiselect("Merchant country codes", cty_options)

# Combined mask
mask = (
    df["transaction_date_time"].dt.date.between(start_date, end_date)
    & (df["merchant_category_code"].isin(mcc_selected) if mcc_selected else True)
    & (df["pos_entry_desc"].isin(pos_selected)         if pos_selected else True)
    & (df["merchant_name"].isin(mn_selected)           if mn_selected else True)
    & (df["fraud_type"].isin(ft_selected)              if ft_selected else True)
    & (df["merchant_country_code"].isin(cty_selected)  if cty_selected else True)
)
view = df[mask]
st.write(f"**{len(view):,} transactions** match your filters.")

# ---------- 4. Quick charts ---------------------------------------------
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

# ---------- 5. Raw-data preview -----------------------------------------
st.subheader("Raw data (first 2 000 rows)")
st.dataframe(view.head(2000), height=300)

# ---------- 6. Candidate input box --------------------------------------
st.text_area(
    "✍️ Paste your key insights & recommended controls here (optional)",
    placeholder="e.g. Contactless fraud spiked 40 % in May; recommend lowering limits…",
    height=150,
)
