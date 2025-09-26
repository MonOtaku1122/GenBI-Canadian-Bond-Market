# dashboard.py
import streamlit as st
import plotly.express as px
import pandas as pd
import google.generativeai as genai

# --- Configure Gemini ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

df_clean = pd.read_csv("df_pivot_cleaned.csv")
df_clean['Year'] = pd.to_datetime(df_clean['REF_DATE']).dt.year

st.set_page_config(page_title="Canadian Bond Market Risk Dashboard", layout="wide")
st.title("📊 Canadian Bond Market Risk Dashboard")

# --- Sidebar Filters ---
st.sidebar.header("Filters")
start_year, end_year = st.sidebar.select_slider(
    "Select Year Range:",
    options=sorted(df_clean['Year'].unique()),
    value=(df_clean['Year'].min(), df_clean['Year'].max()),
    key="year_range_slider"
)

df_filtered = df_clean[
    (df_clean['Year'] >= start_year) & (df_clean['Year'] <= end_year)
].dropna(subset=['2Y_Bond','10Y_Bond','10Y-2Y Spread','10Y_volatility'], how='all')

# --- KPI Cards ---
if not df_filtered.empty:
    latest = df_filtered.iloc[-1]
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("2Y Bond Yield", f"{latest['2Y_Bond']:.2f}%")
    kpi2.metric("10Y Bond Yield", f"{latest['10Y_Bond']:.2f}%")
    kpi3.metric("10Y-2Y Spread", f"{latest['10Y-2Y Spread']:.2f}%")
else:
    st.warning("No data available for the selected year range.")

# --- Visualizations ---
with st.container():
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Yield Curve")
        fig_yield = px.line(df_filtered, x='REF_DATE', y=['2Y_Bond','10Y_Bond'],
                            labels={'value':'Yield (%)','variable':'Bond Maturity'})
        st.plotly_chart(fig_yield, use_container_width=True)

        

    with col2:
        st.subheader("10Y-2Y Spread Over Time")
        
        # Create color column
        df_filtered['Spread_Color'] = df_filtered['10Y-2Y Spread'].apply(lambda x: 'red' if x < 0 else 'green')
        
        # Use color_discrete_map to enforce colors
        fig_spread = px.bar(
            df_filtered,
            x='REF_DATE',
            y='10Y-2Y Spread',
            color='Spread_Color',
            color_discrete_map={'red':'red', 'green':'green'},
            labels={'10Y-2Y Spread':'Yield Spread (%)'},
            title='10Y-2Y Spread (Red = Inverted)'
        )
        
        st.plotly_chart(fig_spread, use_container_width=True)


# --- Gemini Insights ---
st.subheader("📌 Market Insights")
insight_type = st.radio(
    "Insight Type",
    ["Risk Summary", "Investment Recommendation", "Yield Curve Explanation"],
    key="insight_radio"
)

if st.button("🔎 Generate Market Insights", key="gen_insights_button"):
    if not df_filtered.empty:
        latest = df_filtered.iloc[-1]
        prompt = f"""
        Market data for {latest['REF_DATE']}:
        - 2Y Bond Yield: {latest['2Y_Bond']}%
        - 10Y Bond Yield: {latest['10Y_Bond']}%
        - 10Y-2Y Spread: {latest['10Y-2Y Spread']}%
        
        
        Provide a {insight_type.lower()} in plain language for Canadian investors.
        """
        response = model.generate_content(prompt)
        st.success(response.text)
    else:
        st.warning("No data available to generate insights.")
