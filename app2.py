import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="🇮🇳 Indian Startup Funding Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        /* Background and Font */
        .stApp {
            background: linear-gradient(135deg, #fffaf3 0%, #f5e6ca 100%);
            font-family: 'Poppins', sans-serif;
            color: #3b2f2f;
        }

        /* Headings */
        h1, h2, h3, h4 {
            font-family: 'Poppins', sans-serif;
            color: #4b3621;
            font-weight: 600;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f3e5ab 0%, #e8d4a2 100%);
            color: #3b2f2f;
            border-right: 1px solid #d2b48c;
        }

        [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label {
            color: #4b3621 !important;
            font-weight: 500;
        }

        /* KPI Cards */
        .metric-container {
            background: #ffffffd9;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(90, 64, 35, 0.15);
            padding: 25px;
            text-align: center;
            transition: all 0.3s ease;
        }
        .metric-container:hover {
            transform: translateY(-6px);
            box-shadow: 0 6px 20px rgba(90, 64, 35, 0.25);
        }

        /* Typing animation */
        .typing-container {
            display: inline-block;
            border-right: 3px solid #4b3621;
            white-space: nowrap;
            overflow: hidden;
            animation: typing 4s steps(50, end), blink 0.75s step-end infinite;
            font-size: 18px;
            color: #3b2f2f;
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
            background: linear-gradient(to right, #d2b48c, transparent);
            margin: 2rem 0;
        }

        /* Footer */
        footer {
            text-align: center;
            padding: 10px;
            font-size: 14px;
            color: #5a3e1b;
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

# --- KPI SECTION ---
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
    st.subheader("📊 Funding Trend Over Time")
    time_df = df.groupby('Month').agg(Total_Amount=('Amount', 'sum')).reset_index()
    fig = px.line(
        time_df, x='Month', y='Total_Amount',
        template='simple_white',
        markers=True
    )
    fig.update_traces(
        line=dict(color='#8B4513', width=3),
        marker=dict(size=8, color='#d2b48c', line=dict(width=1, color='#4b3621')),
        hovertemplate="<b>%{x}</b><br>Funding: %{y:.2f} M USD"
    )
    fig.update_layout(
        hovermode="x unified",
        plot_bgcolor='#fffaf3',
        paper_bgcolor='#fffaf3',
        font=dict(color='black'),
        xaxis=dict(color='black', showgrid=False),
        yaxis=dict(color='black', showgrid=True, gridcolor='#d2b48c')
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_top_categorical(df, column, title):
    st.subheader(f"🏙️ Top 10 {column}s by Deal Count")
    count_df = df[column].value_counts().nlargest(10).reset_index()
    count_df.columns = [column, 'Deal Count']
    fig = px.bar(
        count_df, x=column, y='Deal Count', color='Deal Count',
        template='simple_white',
        color_continuous_scale='earth'
    )
    fig.update_traces(
        hovertemplate=f"<b>%{{x}}</b><br>Deals: %{{y}}",
        marker_line_color='#4b3621', marker_line_width=1
    )
    fig.update_layout(
        hoverlabel=dict(bgcolor="#f5e6ca", font_size=13, font_color="#3b2f2f"),
        plot_bgcolor='#fffaf3', paper_bgcolor='#fffaf3',
        font=dict(color='black'),
        xaxis=dict(color='black', showgrid=False),
        yaxis=dict(color='black', showgrid=True, gridcolor='#d2b48c')
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_investment_types(df):
    st.subheader("💼 Funding Distribution by Investment Type")
    type_amount = df.groupby('Investment Type')['Amount'].sum().reset_index()
    fig = px.sunburst(
        type_amount, path=['Investment Type'], values='Amount',
        color='Amount', color_continuous_scale='earth'
    )
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Funding: %{value:.2f} M USD",
        textinfo='label+percent entry'
    )
    fig.update_layout(
        margin=dict(t=50, l=0, r=0, b=0),
        paper_bgcolor='#fffaf3',
        font=dict(color='black')
    )
    st.plotly_chart(fig, use_container_width=True)

# --- MAIN APP ---
def main():
    st.title("🤎 Indian Startup Funding Dashboard")

    # Typing animation caption
    st.markdown("""
        <div class="typing-container">
            Gain insights into India's startup ecosystem with funding trends, top sectors, and cities of growth.
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    df = load_data()
    if df.empty:
        return

    # --- Sidebar Filters ---
    st.sidebar.header("🎛️ Filter Data")

    min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
    year_range = st.sidebar.slider("📅 Year Range", min_value=min_year, max_value=max_year, value=(min_year, max_year))

    all_cities = sorted(df['City'].unique().tolist())
    selected_cities = st.sidebar.multiselect("📍 Select Cities", options=all_cities, default=['Bangalore', 'Mumbai', 'Delhi'])

    min_amt, max_amt = float(df['Amount'].min()), float(df['Amount'].max())
    funding_range = st.sidebar.slider("💸 Funding Amount (M USD)", min_value=min_amt, max_value=max_amt, value=(min_amt, max_amt))

    # Apply filters
    filtered_df = df[
        (df['Year'] >= year_range[0]) &
        (df['Year'] <= year_range[1]) &
        (df['City'].isin(selected_cities)) &
        (df['Amount'].between(funding_range[0], funding_range[1]))
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

    st.markdown("<hr><footer>© 2025 | Crafted using Streamlit & Plotly</footer>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()  
