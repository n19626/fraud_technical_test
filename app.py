# app.py – Fraud Trend Analysis Challenge
import streamlit as st
import pandas as pd

# ---------------- 1. Load data ------------------------------------------
@st.cache_data
def load_data():
    return pd.read_csv(
        "data/fraud_dataset_full_final.csv",     # 👈 change if your file name differs
        parse_dates=["transaction_date_time"]
    )

df = load_data()

# ---------------- 2. Page setup -----------------------------------------
st.set_page_config(page_title="Fraud Trend Challenge", page_icon="🕵️", layout="wide")
st.title("🕵️‍♂️ Fraud Trend Analysis – 60-Minute Challenge")

st.markdown(
"""
**Your tasks (60 min)**  

1. Use the filters and charts to explore the data.  
2. Identify **2–3 emerging fraud trends**.  
3. Recommend **2–3 strategic control actions**.  
4. Enter insights in the box below *or* send separately (≤ 300 words).
"""
)

# ---------------- 3. Sidebar filters ------------------------------------
st.sidebar.header("🔍 Quick filters")

# Date range
dmin, dmax = df["transaction_date_time"].dt.date.min(), df["transaction_date_time"].dt.date.max()
d_from, d_to = st.sidebar.date_input("Date range", (dmin, dmax))

# MCC
mcc_sel = st.sidebar.multiselect(
    "Merchant category code (MCC)",
    sorted(df["merchant_category_code"].dropna().unique())
)

# POS entry mode
pos_sel = st.sidebar.multiselect(
    "POS entry mode",
    sorted(df["pos_entry_desc"].dropna().unique())
)

# Merchant name
mn_sel = st.sidebar.multiselect(
    "Merchant names",
    sorted(df["merchant_name"].dropna().unique())
)

# Fraud type
ft_sel = st.sidebar.multiselect(
    "Fraud types",
    sorted([ft for ft in df["fraud_type"].dropna().unique() if ft])
)

# Country
cty_sel = st.sidebar.multiselect(
    "Merchant country codes",
    sorted(df["merchant_country_code"].dropna().unique())
)

# Apply mask
mask = (
    df["transaction_date_time"].dt.date.between(d_from, d_to)
    & (df["merchant_category_code"].isin(mcc_sel) if mcc_sel else True)
    & (df["pos_entry_desc"].isin(pos_sel)         if pos_sel else True)
    & (df["merchant_name"].isin(mn_sel)           if mn_sel else True)
    & (df["fraud_type"].isin(ft_sel)              if ft_sel else True)
    & (df["merchant_country_code"].isin(cty_sel)  if cty_sel else True)
)
view = df[mask]
st.write(f"**{len(view):,} transactions** match your filters.")

fraud_view = view[view["fraud"] == 1]  # only fraud rows for loss charts

# ---------------- 4. KPI / quick charts ---------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Daily fraud rate (%)")
    daily = (
        view.groupby(view["transaction_date_time"].dt.date)["fraud"]
        .mean()
        .mul(100)
        .rename("fraud_rate_%")
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

# ---------------- 5. NEW loss / volume charts ---------------------------
st.markdown("---")
st.header("📊 Fraud-loss dashboards")

# 5-A Monthly fraud losses (amount & volume)
monthly = (
    fraud_view
    .set_index("transaction_date_time")
    .groupby(pd.Grouper(freq="M"))
    .agg(loss_amount_gbp=("transaction_amount", "sum"),
         loss_volume=("fraud", "count"))
)
st.subheader("Monthly fraud losses – GBP")
st.bar_chart(monthly["loss_amount_gbp"])
st.subheader("Monthly fraud volume – count")
st.bar_chart(monthly["loss_volume"])

# 5-B POS entry-mode fraud losses
st.subheader("Fraud losses by POS entry mode (GBP)")
pos_losses = (
    fraud_view
    .groupby("pos_entry_desc")["transaction_amount"]
    .sum()
    .sort_values(ascending=False)
)
st.bar_chart(pos_losses)

# 5-C Secure vs Unsecure fraud losses
st.subheader("Fraud losses – Secure vs Unsecure (GBP)")
sec_losses = (
    fraud_view
    .groupby("secure_indicator")["transaction_amount"]
    .sum()
    .rename_axis("secure_indicator")
)
st.bar_chart(sec_losses)

# 5-D Monthly fraud losses by fraud type (stacked)
st.subheader("Monthly fraud losses by fraud type (GBP)")
by_ft = (
    fraud_view
    .set_index("transaction_date_time")
    .groupby([pd.Grouper(freq="M"), "fraud_type"])["transaction_amount"]
    .sum()
    .unstack(fill_value=0)
)
st.area_chart(by_ft)

# ---------------- 6. Raw-data preview -----------------------------------
st.markdown("---")
st.subheader("Raw data (first 2 000 rows)")
st.dataframe(view.head(2000), height=300)

# ---------------- 7. Candidate input ------------------------------------
st.text_area(
    "✍️ Paste your key insights & recommended controls here (optional)",
    height=150,
)
