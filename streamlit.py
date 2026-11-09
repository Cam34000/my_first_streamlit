

import truststore
truststore.inject_into_ssl()

import streamlit as st
import pandas as pd
import pandas as pd

# --------------------------------------------------
# 1. CONFIGURATION DE L'APPLICATION
# --------------------------------------------------

st.set_page_config(
    page_title="COVID-19 Europe Dashboard",
    page_icon="🦠",
    layout="wide"
)

st.title("🦠 COVID-19 Dashboard - Europe")
st.markdown(
    """
    Explore the evolution of COVID-19 cases and deaths
    across European countries using ECDC historical data.
    """
)

# --------------------------------------------------
# 2. CHARGEMENT DES DONNEES
# --------------------------------------------------

URL = (
    "https://opendata.ecdc.europa.eu/"
    "covid19/nationalcasedeath_eueea_daily_ei/csv"
)

@st.cache_data
def load_data():

    df = pd.read_csv(
        URL,
        encoding="utf-8-sig"
    )

    # Convert date column
    df["dateRep"] = pd.to_datetime(
        df["dateRep"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    # Convert numerical columns
    df["cases"] = pd.to_numeric(
        df["cases"], errors="coerce"
    )

    df["deaths"] = pd.to_numeric(
        df["deaths"], errors="coerce"
    )

    # Remove rows without a valid date
    df = df.dropna(subset=["dateRep"])

    # Sort by date
    df = df.sort_values("dateRep")

    return df


try:
    df = load_data()

except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()


# --------------------------------------------------
# 3. SIDEBAR - FILTERS
# --------------------------------------------------

st.sidebar.header("Filters")

# Country selection
countries = sorted(
    df["countriesAndTerritories"].dropna().unique()
)

default_country = (
    ["France"] if "France" in countries
    else [countries[0]]
)

selected_countries = st.sidebar.multiselect(
    "Select countries",
    options=countries,
    default=default_country
)

# Date selection
min_date = df["dateRep"].min().date()
max_date = df["dateRep"].max().date()

date_range = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Indicator selection
indicator = st.sidebar.selectbox(
    "Select an indicator",
    options=["cases", "deaths"],
    format_func=lambda x: {
        "cases": "New cases",
        "deaths": "New deaths"
    }[x]
)


# --------------------------------------------------
# 4. FILTER DATA
# --------------------------------------------------

if len(selected_countries) == 0:
    st.warning("Please select at least one country.")
    st.stop()

if len(date_range) != 2:
    st.warning("Please select a start and end date.")
    st.stop()

start_date, end_date = date_range

filtered_df = df[
    (df["countriesAndTerritories"].isin(selected_countries))
    & (df["dateRep"].dt.date >= start_date)
    & (df["dateRep"].dt.date <= end_date)
].copy()


if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()


# --------------------------------------------------
# 5. KEY PERFORMANCE INDICATORS (KPIs)
# --------------------------------------------------

st.subheader("📊 Key indicators")

total_cases = filtered_df["cases"].sum()
total_deaths = filtered_df["deaths"].sum()

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total cases",
    f"{total_cases:,.0f}"
)

col2.metric(
    "Total deaths",
    f"{total_deaths:,.0f}"
)

col3.metric(
    "Countries selected",
    len(selected_countries)
)


# --------------------------------------------------
# 6. TIME SERIES ANALYSIS
# --------------------------------------------------

st.subheader("📈 Evolution over time")

st.caption(
    "Daily evolution of the selected indicator "
    "for the selected countries."
)

# Aggregate data by date and country
time_series = (
    filtered_df
    .groupby(["dateRep", "countriesAndTerritories"])[indicator]
    .sum()
    .reset_index()
)

# Pivot for Streamlit line chart
chart_data = time_series.pivot(
    index="dateRep",
    columns="countriesAndTerritories",
    values=indicator
)

chart_data = chart_data.sort_index()

st.line_chart(chart_data)


# --------------------------------------------------
# 7. COUNTRY COMPARISON
# --------------------------------------------------

st.subheader("🌍 Country comparison")

country_comparison = (
    filtered_df
    .groupby("countriesAndTerritories")[["cases", "deaths"]]
    .sum()
    .sort_values(indicator, ascending=False)
)

st.bar_chart(
    country_comparison[indicator]
)

st.dataframe(
    country_comparison,
    use_container_width=True
)


# --------------------------------------------------
# 8. RAW DATA EXPLORATION
# --------------------------------------------------

st.subheader("🔎 Explore the dataset")

st.write(
    f"Number of observations: {len(filtered_df):,}"
)

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 9. DOWNLOAD FILTERED DATA
# --------------------------------------------------

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download filtered data",
    data=csv,
    file_name="covid19_filtered_data.csv",
    mime="text/csv"
)


# --------------------------------------------------
# 10. FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Source: European Centre for Disease Prevention "
    "and Control (ECDC) - Historical dataset."
)

st.caption(
    "This dataset is archived and is no longer updated "
    "since November 2022."
)
