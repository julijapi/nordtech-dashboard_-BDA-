import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ---------------------------------
# Lapas konfigurācija
# ---------------------------------
st.set_page_config(page_title="NordTech – Datu pārskats", layout="wide")

# ---------------------------------
# Datu ielāde
# ---------------------------------
df = pd.read_csv("enriched_data.csv")
df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

# ---------------------------------
# Teksta lauku normalizācija (lai nebūtu dublikātu kategorijās)
# ---------------------------------
def normalize_text(x):
    if pd.isna(x):
        return ""
    x = str(x)
    x = x.replace("\u00A0", " ")          # non-breaking space -> space
    x = re.sub(r"\s+", " ", x)            # vairāki tukšumi -> viens
    x = x.strip()                          # noņem tukšumus sākumā/beigās
    return x

df["Product_Category"] = df["Product_Category"].apply(normalize_text).str.title()
df["Product_Name"] = df["Product_Name"].apply(normalize_text)

# ---------------------------------
# Sidebar filtri
# ---------------------------------
st.sidebar.header("Filtri")

months = sorted(df["month"].dropna().unique())
selected_months = st.sidebar.multiselect(
    "Izvēlies periodu (mēnesi)",
    months,
    default=months
)

categories = sorted([c for c in df["Product_Category"].dropna().unique() if c != ""])
selected_categories = st.sidebar.multiselect(
    "Izvēlies produktu kategoriju",
    categories,
    default=categories
)

filtered_df = df[
    (df["month"].isin(selected_months)) &
    (df["Product_Category"].isin(selected_categories))
].copy()

# ---------------------------------
# KPI rinda
# ---------------------------------
st.title("NordTech – Pārdošana, atgriezumi un klientu signāli")

col1, col2, col3 = st.columns(3)

total_revenue = filtered_df["revenue_eur"].sum()
refund_sum = filtered_df["total_refund_eur"].sum()
return_rate = filtered_df["return_flag"].mean() * 100

col1.metric("Kopējie ieņēmumi (EUR)", f"{total_revenue:,.2f}")
col2.metric("Atgriezumu īpatsvars (%)", f"{return_rate:.2f}")
col3.metric("Kopējā atgrieztā summa (EUR)", f"{refund_sum:,.2f}")

# ---------------------------------
# Grafiks 1: Ieņēmumi laikā
# ---------------------------------
revenue_by_month = (
    filtered_df
    .groupby("month", as_index=False)["revenue_eur"]
    .sum()
)

fig1 = px.line(
    revenue_by_month,
    x="month",
    y="revenue_eur",
    title="Ieņēmumu dinamika laikā",
    markers=True
)
st.plotly_chart(fig1, use_container_width=True)

# ---------------------------------
# Grafiks 2: Atgriezumi pēc produktu kategorijām (bez dublikātiem)
# ---------------------------------
returns_by_category = (
    filtered_df[filtered_df["return_flag"] == 1]
    .groupby("Product_Category", as_index=False)
    .agg(return_count=("return_flag", "count"))
    .sort_values("return_count", ascending=False)
)

fig2 = px.bar(
    returns_by_category,
    x="Product_Category",
    y="return_count",
    title="Atgriezumu sadalījums pēc produktu kategorijām",
    text="return_count"
)
st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------
# Tabula: Top problem cases
# ---------------------------------
st.subheader("Top produkti pēc atgriezumiem")

top_products = (
    filtered_df[filtered_df["return_flag"] == 1]
    .groupby("Product_Name", as_index=False)
    .agg(
        atgriezumu_skaits=("return_flag", "count"),
        atgriezta_summa=("total_refund_eur", "sum")
    )
    .sort_values(["atgriezumu_skaits", "atgriezta_summa"], ascending=False)
)

st.dataframe(top_products, use_container_width=True)