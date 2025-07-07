# app.py  – Fraud Trend Analysis Challenge (global-heatmap version)
import streamlit as st
import pandas as pd
import pydeck as pdk

# ---------- 1. Load data (drop VELOCITY + unwanted columns) ----------------
@st.cache_data
def load_data():
    df = (
        pd.read_csv(
            "data/fraud_dataset_full_final.csv",        # <-- adjust if filename differs
            parse_dates=["transaction_date_time"]
        )
        # exclude VELOCITY fraud-type rows
        .query("fraud_type.str.upper() != 'VELOCITY'", engine="python")
        # drop the unneeded transaction-type columns
        .drop(columns=["transaction_type_code", "transaction_type_desc"],
              errors="ignore")
    )
    return df

df = load_data()

# ---------- 2. Page setup ---------------------------------------------
st.set_page_config(page_title="Fraud Trend Analysis",
                   page_icon="🕵️",
                   layout="wide")
st.title("🕵️‍♂️ Fraud Trend Analysis – 60-Minute Challenge")
st.markdown(
"""
**Your tasks (45 min)**  

1. Explore the data with the filters and charts below (Raw data can be exported and other offline tools can be used)  
2. Identify **3-5 emerging fraud trends**.  
3. Recommend **3-5 strategic controls**.  
4. Discuss findings (15 min)
"""
)

# ---------- 3. Sidebar filters ----------------------------------------
st.sidebar.header("🔍 Quick filters")

date_min = df["transaction_date_time"].dt.date.min()
date_max = df["transaction_date_time"].dt.date.max()
start_date, end_date = st.sidebar.date_input("Date range", (date_min, date_max))

mcc_opts = sorted(df["merchant_category_code"].dropna().unique())
pos_opts = sorted(df["pos_entry_desc"].dropna().unique())
mn_opts  = sorted(df["merchant_name"].dropna().unique())
ft_opts  = sorted([ft for ft in df["fraud_type"].dropna().unique() if ft])
cty_opts = sorted(df["merchant_country_code"].dropna().unique())

mcc_sel = st.sidebar.multiselect("Merchant category code (MCC)", mcc_opts)
pos_sel = st.sidebar.multiselect("POS entry mode", pos_opts)
mn_sel  = st.sidebar.multiselect("Merchant names", mn_opts)
ft_sel  = st.sidebar.multiselect("Fraud types", ft_opts)
cty_sel = st.sidebar.multiselect("Merchant country codes", cty_opts)

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

# ---------- 4. Daily loss table with monthly cumulative ---------------
fraud_view = view[view["fraud"] == 1].copy()
fraud_view["date"]  = fraud_view["transaction_date_time"].dt.date
fraud_view["month"] = fraud_view["transaction_date_time"].dt.to_period("M").astype(str)

daily = (
    fraud_view.groupby(["date", "month"])
    .agg(fraud_volume=("fraud", "count"),
         fraud_value=("transaction_amount", "sum"))
    .reset_index()
)
daily["month_cum_volume"] = daily.groupby("month")["fraud_volume"].cumsum()
daily["month_cum_value"]  = daily.groupby("month")["fraud_value"].cumsum()

st.subheader("🗓️ Daily fraud losses with monthly cumulative")
st.dataframe(daily, height=300)

# ---------- 5. Charts ---------------------------------------------------
col1, col2 = st.columns(2)

# 5a. Daily fraud-rate %
with col1:
    st.subheader("📈 Daily fraud rate (%)")
    daily_rate = (
        view.groupby(view["transaction_date_time"].dt.date)["fraud"]
        .mean()
        .mul(100)
        .rename("fraud_rate_%")
    )
    st.line_chart(daily_rate)

# 5b. Fraud rate by country
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

# 5c. Monthly fraud £ by POS entry
st.subheader("💳 Monthly fraud value by POS entry (£)")
fraud_month_pos = (
    fraud_view
    .groupby([fraud_view["transaction_date_time"].dt.to_period("M").astype(str),
              "pos_entry_desc"])["transaction_amount"]
    .sum()
    .unstack(fill_value=0)
)
st.line_chart(fraud_month_pos)

# 5d. Global heat-map of fraud volume -----------------------------------
st.subheader("🌍 Global fraud hotspots")

# rough lat/lon centroids for ISO-2 country codes used in the dataset
country_coords = {
    "GB": (54.0,  -2.0),  "US": (39.5, -98.35), "CA": (56.1, -106.3),
    "FR": (46.2,   2.2),  "DE": (51.1,  10.4),  "NL": (52.1,   5.3),
    "IE": (53.1,  -8.2),  "ES": (40.5,  -3.7),  "IT": (42.8,  12.5),
    "AU": (-25.3, 133.8), "NZ": (-41.0, 174.0), "IN": (22.6,  78.9),
    "CN": (35.9, 104.2),  "JP": (36.2, 138.2),  "HK": (22.3, 114.2),
    "SG": ( 1.3, 103.8),  "KR": (36.5, 127.9),  "MY": ( 4.2, 101.9),
    "TH": (15.9, 100.9),  "PH": (12.9, 122.9), "BR": (-14.2, -51.9),
    "MX": (23.6, -102.6), "AR": (-38.4, -63.6), "ZA": (-28.5,  24.7),
    "KE": ( -0.0,  37.9), "NG": ( 9.1,   8.7), "GH": ( 7.9,  -1.0),
    "EG": (26.8,  29.8),  "RU": (61.5, 105.3), "UA": (48.4,  31.1),
    "IR": (32.5,  53.7),  "PK": (30.4,  69.3), "TR": (38.9,  35.2),
    "AE": (24.2,  54.7),  "SA": (24.1,  45.0), "QA": (25.3,  51.2),
    "CO": ( 4.6, -74.1),  "CL": (-30.0, -71.0), "PE": (-9.2, -75.0),
    "ID": ( -2.3, 118.0)
}

# aggregate fraud volume per country
country_vol = (
    fraud_view.groupby("merchant_country_code")["fraud"]
    .count()
    .reset_index(name="fraud_volume")
)
# attach lat/lon
country_vol["lat"] = country_vol["merchant_country_code"].map(lambda c: country_coords.get(c, (None, None))[0])
country_vol["lon"] = country_vol["merchant_country_code"].map(lambda c: country_coords.get(c, (None, None))[1])
country_vol = country_vol.dropna(subset=["lat", "lon"])

# create heat-map layer
layer = pdk.Layer(
    "HeatmapLayer",
    data=country_vol,
    get_position="[lon, lat]",
    get_weight="fraud_volume",
    radiusPixels=60,
    aggregation=pdk.types.String("SUM"),
)

view_state = pdk.ViewState(latitude=15, longitude=0, zoom=1)
deck = pdk.Deck(layers=[layer], initial_view_state=view_state,
                tooltip={"text": "{merchant_country_code}: {fraud_volume}"})
st.pydeck_chart(deck)

# ---------- 6. Raw-data preview ---------------------------------------
st.subheader("Raw data (10k transactions)")
st.dataframe(view.head(10000), height=300)
