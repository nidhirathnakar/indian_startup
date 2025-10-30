import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="🇮🇳 Indian Startup Funding Dashboard",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        /* Background */
        .stApp {
            background: linear-gradient(135deg, #f9fafc 0%, #eef2f7 100%);
            font-family: 'Poppins', sans-serif;
            color: #222;
        }

        /* Headings */
        h1, h2, h3, h4 {
            font-family: 'Poppins', sans-serif;
            color: #1a1a1a;
            font-weight: 600;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e0e0e0;
        }

        /* KPI Cards */
        .metric-container {
            background-color: white;
            border-radius: 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            padding: 20px;
            text-align: center;
            transition: transform 0.2s ease;
        }
        .metric-container:hover {
            transform: translateY(-5px);
        }

        /* Typing animation */
        .typing-container {
            display: inline-block;
            border-right: 3px solid #333;
            white-space: nowrap;
            overflow: hidden;
            animation: typing 4s steps(50, end), blink 0.75s step-end infinite;
            font-size: 18px;
            color: #333;
            font-family: 'Poppins', sans-serif;
            margin-top: -10px;
        }

        @keyframes typing {
            from { width: 0; }
            to { width: 100%; }
        }

        @keyframes blink {
            50% { border-color: transparent; }
        }

        /* Dividers */
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(to right, #c7c7c7, transparent);
            margin: 2rem 0;
        }

        /* Footer */
        footer {
            text-align: center;
            padding: 10px;
            font-size: 14px;
            color: #777;
        }
    </style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    try:
        data = pd.read_csv("merged.csv.csv", encoding='ISO-8859-1', header=4)
    except:
        st.error("⚠️ Couldn't load 'merged.csv.csv'. Please ensure the file is in the same directory.")
        return pd.DataFrame()

    try:
        df = data.iloc[:, [13, 14, 15, 17, 19, 20]].copy()
        df.columns = ['Date', 'Startup Name', 'Sector', 'City', 'Investment Type', 'Amount']
    except IndexError:
        st.error("Column mismatch. Please check your CSV format.")
        return pd.DataFrame()

    def clean_amount(x):
        if isinstance(x, str):
            x = x.replace(',', '').replace('$', '').strip().lower()
            if any(u in x for u in ['lac', 'lakh', 'cr', 'unknown', 'n/a']):
                return np.nan
        try:
            return float(x) / 1_000_000
        except:
            return np.nan

    df['Amount'] = df['Amount'].apply(clean_amount)
    df.dropna(subset=['Amount'], inplace=True)
    df = df[df['Amount'] > 0]

    def clean_date(d):
        try:
            return datetime.strptime(str(d).strip(), '%d/%m/%Y')
        except:
            return pd.NaT

    df['Date'] = df['Date'].apply(clean_date)
    df.dropna(subset=['Date'], inplace=True)
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.to_period('M').astype(str)

    text_cols = ['Sector', 'City', 'Investment Type', 'Startup Name']
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip().str.title().replace({'Nan': 'Other', 'N/A': 'Other'})
        if col == 'City':
            df[col] = df[col].replace({
                'Bengaluru': 'Bangalore', 
                'New Delhi': 'Delhi', 
                'Gurugram': 'Gurgaon', 
                'Hydrabad': 'Hyderabad'
            })
        if col == 'Investment Type':
            df[col] = df[col].replace({'Seed/ Angel Funding': 'Seed/Angel Funding'})

    df = df[df['Amount'] < 1000]
    return df

# --- KPIs ---
def display_kpis(df):
    total_funding = df['Amount'].sum()
    total_startups = df['Startup Name'].nunique()
    avg_funding = df['Amount'].mean()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-container'><h3>💰 Total Funding</h3><h2>{total_funding:,.2f} M USD</h2></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-container'><h3>🚀 Total Startups</h3><h2>{total_startups:,}</h2></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-container'><h3>📈 Avg. Investment</h3><h2>{avg_funding:,.2f} M USD</h2></div>", unsafe_allow_html=True)

# --- PLOTS ---
def plot_funding_over_time(df):
    time_df = df.groupby('Month').agg(Total_Amount=('Amount', 'sum')).reset_index()
    fig = px.area(time_df, x='Month', y='Total_Amount',
                  title='📊 Funding Trend Over Time',
                  template='plotly_white', color_discrete_sequence=['#636EFA'])
    fig.update_traces(mode='lines+markers', line=dict(width=3))
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

def plot_top_categorical(df, column, title):
    count_df = df[column].value_counts().nlargest(10).reset_index()
    count_df.columns = [column, 'Deal Count']
    fig = px.bar(count_df, x=column, y='Deal Count', color='Deal Count',
                 title=f"🏙️ Top 10 {column}s by Deal Count", template='plotly_white',
                 color_continuous_scale='Blues')
    fig.update_layout(xaxis=dict(tickangle=45))
    st.plotly_chart(fig, use_container_width=True)

def plot_investment_types(df):
    type_amount = df.groupby('Investment Type')['Amount'].sum().reset_index()
    fig = px.pie(type_amount, values='Amount', names='Investment Type',
                 title='💼 Funding Share by Investment Type', template='plotly_white',
                 color_discrete_sequence=px.colors.sequential.RdBu)
    fig.update_traces(textinfo='percent+label', pull=[0.05]*len(type_amount))
    st.plotly_chart(fig, use_container_width=True)

# --- MAIN ---
def main():
    st.title("🇮🇳 Indian Startup Funding Dashboard")

    # ✨ Typing animation caption
    st.markdown("""
        <div class="typing-container">
            An elegant overview of startup funding trends across India.
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    df = load_data()
    if df.empty:
        return

    st.sidebar.header("🎛️ Filter Data")
    min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
    year_range = st.sidebar.slider("Select Year Range", min_value=min_year, max_value=max_year, value=(min_year, max_year))
    
    top_cities = df['City'].value_counts().nlargest(10).index.tolist()
    all_cities = sorted(df['City'].unique().tolist())
    default_cities = [c for c in top_cities if c in all_cities and c != 'Other']
    selected_cities = st.sidebar.multiselect("Select Cities", options=all_cities, default=default_cities)
    
    filtered_df = df[
        (df['Year'] >= year_range[0]) &
        (df['Year'] <= year_range[1]) &
        (df['City'].isin(selected_cities))
    ]

    st.markdown(f"### Showing results for **{filtered_df['Startup Name'].nunique():,}** startups.")
    st.markdown("<hr>", unsafe_allow_html=True)

    if filtered_df.empty:
        st.warning("⚠️ No data matches your filters.")
        return

    display_kpis(filtered_df)
    st.markdown("<hr>", unsafe_allow_html=True)
    plot_funding_over_time(filtered_df)
    st.markdown("<hr>", unsafe_allow_html=True)
    plot_top_categorical(filtered_df, 'City', "City Analysis")
    st.markdown("<hr>", unsafe_allow_html=True)
    plot_top_categorical(filtered_df, 'Sector', "Sector Analysis")
    st.markdown("<hr>", unsafe_allow_html=True)
    plot_investment_types(filtered_df)

    st.markdown("<hr><footer>@2025 | Built using Streamlit & Plotly</footer>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
