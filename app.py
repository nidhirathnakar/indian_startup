import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import re

# --- CONFIGURATION ---
st.set_page_config(
    page_title="🇮🇳 Indian Startup Funding Analysis Dashboard",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONSTANTS ---
DATA_FILE_NAME = "merged.csv.csv"

# --- DATA LOADING AND CLEANING ---

@st.cache_data
def load_data():
    """
    Loads, cleans, and transforms the raw startup funding data.
    - Uses header=4 to skip initial metadata rows.
    - Targets columns by index to handle inconsistent names in the merged CSV.
    """
    try:
        # Load header from index 4 (5th line).
        data = pd.read_csv(DATA_FILE_NAME, encoding='ISO-8859-1', header=4)
    except Exception as e:
        st.error("Error loading the CSV file. Please ensure 'merged.csv.csv' is in the same directory.")
        return pd.DataFrame()

    # --- Column Selection by Index ---
    # Based on the snippet:
    # 13: Sr No (not needed)
    # 14: Date dd/mm/yyyy (Index 13) -> Our Date
    # 15: Startup Name (Index 14) -> Our Startup Name
    # 16: Industry Vertical (Index 15) -> Our Sector
    # 17: SubVertical (Index 16) -> Not needed
    # 18: City Location (Index 17) -> Our City
    # 19: Investors Name (Index 18) -> Not needed
    # 20: InvestmentnType (Index 19) -> Our Investment Type
    # 21: Amount in USD (Index 20) -> Our Amount

    # Select columns by their 0-based index: 13, 14, 15, 17, 19, 20
    try:
        df = data.iloc[:, [13, 14, 15, 17, 19, 20]].copy()
        df.columns = ['Date', 'Startup Name', 'Sector', 'City', 'Investment Type', 'Amount']
    except IndexError:
        st.error("Column selection failed. The funding data might not start at the expected column index (13). Please check your CSV file again.")
        return pd.DataFrame()


    # 1. Clean 'Amount' column and convert to millions (USD)
    def clean_amount(x):
        """Removes non-numeric chars and converts to float."""
        if isinstance(x, str):
            x = x.replace(',', '').replace('$', '').replace('nan', '').strip()
            # Drop rows with non-USD funding formats (e.g., 'cr' or 'lakh')
            if 'lac' in x.lower() or 'lakh' in x.lower() or 'cr' in x.lower() or 'unknown' in x.lower():
                return np.nan 
            if x.lower() == 'n/a' or not x:
                return np.nan
        try:
            return float(x) / 1000000  # Convert USD to Million USD
        except:
            return np.nan

    df['Amount'] = df['Amount'].apply(clean_amount)
    # Drop rows where Amount is NaN or zero (no funding recorded)
    df.dropna(subset=['Amount'], inplace=True)
    df = df[df['Amount'] > 0].copy()
    
    # 2. Clean 'Date' column and create time-based features
    def clean_date(date_str):
        """Converts dd/mm/yyyy string to datetime object."""
        try:
            return datetime.strptime(str(date_str).strip(), '%d/%m/%Y')
        except ValueError:
            return pd.NaT # Not a Time

    df['Date'] = df['Date'].apply(clean_date)
    df.dropna(subset=['Date'], inplace=True)
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.to_period('M').astype(str)

    # 3. Clean other categorical columns
    text_cols = ['Sector', 'City', 'Investment Type', 'Startup Name']
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip().str.title().replace({'Nan': 'Other', 'N/A': 'Other', 'Nan/Nan': 'Other'})
        df[col].replace('', 'Other', inplace=True)
        # Further clean-up for common merged names/typos
        if col == 'City':
            df[col] = df[col].replace({'Bengaluru': 'Bangalore', 'New Delhi': 'Delhi', 'Gurugram': 'Gurgaon', 'Hydrabad': 'Hyderabad'})
        if col == 'Investment Type':
             df[col] = df[col].replace({'Seed/ Angel Funding': 'Seed/Angel Funding', 'Private Equity': 'Private Equity/Venture Capital'})
            
    # Remove large outliers (e.g., funding > $1 Billion) for better chart scaling
    df = df[df['Amount'] < 1000].copy()

    return df

# --- METRICS & VISUALIZATIONS ---

def display_kpis(df):
    """Displays key performance indicators in columns."""
    total_funding = df['Amount'].sum()
    total_startups = df['Startup Name'].nunique()
    avg_funding = df['Amount'].mean()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Funding (M USD)", f"{total_funding:,.2f}")
    col2.metric("🚀 Total Startups Funded", f"{total_startups:,}")
    col3.metric("📈 Avg. Investment Size (M USD)", f"{avg_funding:,.2f}")

def plot_funding_over_time(df):
    """Plots total funding and number of deals over time."""
    time_df = df.groupby('Month').agg(
        Total_Amount=('Amount', 'sum'),
        Deal_Count=('Startup Name', 'count')
    ).reset_index()

    st.subheader("Funding Trend Over Time")
    
    fig_amount = px.line(
        time_df,
        x='Month',
        y='Total_Amount',
        title='Total Funding (M USD) by Month',
        labels={'Total_Amount': 'Total Funding (M USD)'},
        template='plotly_white'
    )
    fig_amount.update_xaxes(tickangle=45, nticks=20)
    st.plotly_chart(fig_amount, use_container_width=True)

    fig_deals = px.bar(
        time_df,
        x='Month',
        y='Deal_Count',
        title='Number of Deals by Month',
        labels={'Deal_Count': 'Number of Deals'},
        template='plotly_white'
    )
    fig_deals.update_xaxes(tickangle=45, nticks=20)
    st.plotly_chart(fig_deals, use_container_width=True)


def plot_top_categorical(df, column, title):
    """Plots Top 10 by count and sum for a given categorical column."""
    st.subheader(title)
    
    # Group by Count (Deal Volume)
    count_df = df[column].value_counts().nlargest(10).reset_index()
    count_df.columns = [column, 'Deal Count']
    fig_count = px.bar(
        count_df,
        x=column,
        y='Deal Count',
        title=f"Top 10 {column} by Deal Count",
        template='plotly_white',
        color='Deal Count'
    )
    st.plotly_chart(fig_count, use_container_width=True)
    
    # Group by Amount (Funding Volume)
    amount_df = df.groupby(column)['Amount'].sum().nlargest(10).reset_index()
    amount_df.columns = [column, 'Total Funding (M USD)']
    fig_amount = px.bar(
        amount_df,
        x=column,
        y='Total Funding (M USD)',
        title=f"Top 10 {column} by Total Funding (M USD)",
        template='plotly_white',
        color='Total Funding (M USD)'
    )
    st.plotly_chart(fig_amount, use_container_width=True)

def plot_investment_types(df):
    """Plots funding distribution by Investment Type."""
    st.subheader("Funding Distribution by Investment Type")
    
    # By Funding Amount
    type_amount = df.groupby('Investment Type')['Amount'].sum().reset_index()
    fig = px.pie(
        type_amount,
        values='Amount',
        names='Investment Type',
        title='Funding Amount Share by Investment Type',
        template='plotly_white'
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
    
# --- MAIN APP FUNCTION ---
def main():
    st.title("🇮🇳 Indian Startup Funding Dashboard")
    
    df = load_data()
    
    if df.empty:
        return

    # --- SIDEBAR FOR FILTERING ---
    st.sidebar.header("Filter Data")
    
    # Year Slider Filter
    min_year = int(df['Year'].min())
    max_year = int(df['Year'].max())
    year_range = st.sidebar.slider(
        'Select Year Range',
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    
    # City Multi-select Filter (Top 10 by deals by default)
    top_cities = df['City'].value_counts().nlargest(10).index.tolist()
    all_cities = sorted(df['City'].unique().tolist())
    # Exclude 'Other' from default selection
    default_cities = [city for city in top_cities if city in all_cities and city != 'Other']

    selected_cities = st.sidebar.multiselect(
        'Select Cities',
        options=all_cities,
        default=default_cities
    )
    
    # Apply Filters
    filtered_df = df[
        (df['Year'] >= year_range[0]) & 
        (df['Year'] <= year_range[1]) &
        (df['City'].isin(selected_cities))
    ]
    
    st.write(f"Displaying data for **{filtered_df['Startup Name'].nunique():,}** unique startups.")

    if filtered_df.empty:
        st.warning("No data matches the selected filters.")
        return

    st.markdown("---")
    
    # Display KPIs
    display_kpis(filtered_df)
    
    st.markdown("---")
    
    # Time Series Analysis
    plot_funding_over_time(filtered_df)
    
    st.markdown("---")

    # Categorical Analysis (City)
    plot_top_categorical(filtered_df, 'City', "City Analysis")

    st.markdown("---")

    # Categorical Analysis (Sector)
    plot_top_categorical(filtered_df, 'Sector', "Sector Analysis")

    st.markdown("---")

    # Investment Type Analysis
    plot_investment_types(filtered_df)

if __name__ == "__main__":
    main()