# app.py  – Fraud Trend Analysis Challenge  (feedback version)
import streamlit as st
import pandas as pd

# ---------- 1. Load data -------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(
        "data/fraud_dataset_full_final.csv",            # ← adjust name if needed
        parse_dates=["transaction_date_time"]
    )
    # drop VELOCITY fraud rows entirely
    df = df[df["fraud_type"].fillna("").str.upper() != "VELOCITY"]
    return df

df = load_data()

# ---------- 2. Page setup ------------------------------------------------
st.set_page_config(
    page_title="Fraud Trend Analysis Challenge",
    page_icon="🕵️",
    layout="wide",
)
st.title("🕵️‍♂️ Fraud Trend Analysis – 60-Minute Challenge")
st.markdown(
"""
**Your tasks (60 min)**  

1. Explore the data with the filters and charts below.  
2. Identify **2–3 emerging fraud trends**.  
3. Recommend **2–3 strategic controls** (submit separately).  
"""
)

# ---------- 3. Sidebar filters ------------------------------------------
st.sidebar.header("🔍 Quick filters")

# Date range
date_min = df["transaction_date_time"].dt.date.min()
date_max = df["transaction_date_time"].dt.date.max()
start_date, end_date = st.sidebar.date_input(
    "Date range", (date_min, date_max)
)

# Merchant Category Code
mcc_opts = sorted(df["merchant_category_code"].dropna().unique())
mcc_sel  = st.sidebar.multiselect("Merchant category code (MCC)", mcc_opts)

# POS Entry Mode
pos_opts = sorted(df["pos_entry_desc"].dropna().unique())
pos_sel  = st.sidebar.multiselect("POS entry mode", pos_opts)

# Merchant Name
mn_opts  = sorted(df["merchant_name"].dropna().unique())
mn_sel   = st.sidebar.multiselect("Merchant names", mn_opts)

# Fraud Type  (VELOCITY already removed)
ft_opts  = sorted([ft for ft in df["fraud_type"].dropna().unique() if ft])
ft_sel   = st.sidebar.multiselect("Fraud types", ft_opts)

# Merchant Country
cty_opts = sorted(df["merchant_country_code"].dropna().unique())
cty_sel  = st.sidebar.multiselect("Merchant country codes", cty_opts)

mask = (
    df["transaction_date_time"].dt.date.between(start_date, end_date)
    & (df["merchant_category_code"].isin(mcc_sel) if mcc_sel else True)
    & (df["pos_entry_desc"].isin(pos_sel)         if pos_sel else True)
    & (df["merchant_name"].isin(mn_sel)           if mn_sel else True)
    & (df["fraud_type"].isin(ft_sel)              if ft_sel else True)
    & (df["merchant_country_code"].isin(cty_sel)  if cty_sel else True)
)
view = df[mask]
st.write(f"**{len(view):,} transactions** match your filters.")

# ---------- 4. Daily & monthly cumulative fraud loss table --------------
fraud_view = view[view["fraud"] == 1].copy()
fraud_view["date"]  = fraud_view["transaction_date_time"].dt.date
fraud_view["month"] = fraud_view["transaction_date_time"].dt.to_period("M").astype(str)

daily = (fraud_view
         .groupby(["date", "month"])
         .agg(fraud_volume=("fraud", "count"),
              fraud_value=("transaction_amount", "sum"))
         .reset_index())

# cumulative by month
daily["month_cum_volume"] = daily.groupby("month")["fraud_volume"].cumsum()
daily["month_cum_value"]  = daily.groupby("month")["fraud_value"].cumsum()

st.subheader("🗓️ Daily fraud losses with monthly cumulative")
st.dataframe(daily, height=300)

# ---------- 5. Line chart – fraud losses by POS entry (monthly) ----------
fraud_month_pos = (
    fraud_view
    .groupby([fraud_view["transaction_date_time"].dt.to_period("M").astype(str),
              "pos_entry_desc"])["transaction_amount"]
    .sum()
    .unstack(fill_value=0)
)

st.subheader("📊 Monthly fraud value by POS entry mode (£)")
st.line_chart(fraud_month_pos)

# ---------- 6. Raw-data preview -----------------------------------------
st.subheader("Raw data (first 2 000 rows)")
st.dataframe(view.head(2000), height=300)
