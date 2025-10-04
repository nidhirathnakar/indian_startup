import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Indian Startup Funding Dashboard", layout="wide")

# -------------------- Load and Clean Data -------------------- #
@st.cache_data
def load_data():
    data = pd.read_csv("startup_funding.csv")
    data.columns = data.columns.str.strip()

    # Rename date column variations
    if 'Date' not in data.columns:
        for col in data.columns:
            if 'date' in col.lower():  # handles 'Date', 'date', etc.
                data.rename(columns={col: 'Date'}, inplace=True)
                break
        else:
            raise KeyError("No 'Date' column found in the dataset.")

    # Remove bad date entries like '#####'
    data = data[data['Date'].str.match(r'\d{1,2}/\d{1,2}/\d{2,4}') == True]

    # Convert Date column to datetime
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    data = data.dropna(subset=['Date'])

    # Convert Amount in USD to numeric
    if 'Amount in USD' in data.columns:
        data['Amount in USD'] = pd.to_numeric(data['Amount in USD'], errors='coerce')

    # Strip whitespace in string columns
    str_cols = data.select_dtypes(['object']).columns
    for col in str_cols:
        data[col] = data[col].str.strip()

    return data

df = load_data()

# -------------------- Streamlit App -------------------- #
st.title("🇮🇳 Indian Startup Funding Analysis Dashboard")

# Sidebar filters
st.sidebar.header("Filters")
year_range = st.sidebar.slider("Select Year Range:", int(df['Date'].dt.year.min()), int(df['Date'].dt.year.max()),
                               (int(df['Date'].dt.year.min()), int(df['Date'].dt.year.max())))
selected_years = df[(df['Date'].dt.year >= year_range[0]) & (df['Date'].dt.year <= year_range[1])]

# Show raw data
if st.sidebar.checkbox("Show Raw Data"):
    st.subheader("Raw Dataset")
    st.dataframe(selected_years)

# -------------------- Total Investment Over Years -------------------- #
st.subheader("📊 Total Investment Over the Years")
yearwise = selected_years.groupby(selected_years['Date'].dt.year)['Amount in USD'].sum()
st.bar_chart(yearwise)

# -------------------- Top 10 Funded Startups -------------------- #
st.subheader("🚀 Top 10 Funded Startups")
if 'Startup Name' in df.columns:
    top_startups = selected_years.groupby('Startup Name')['Amount in USD'].sum().sort_values(ascending=False).head(10)
    st.bar_chart(top_startups)
else:
    st.warning("'Startup Name' column not found!")

# -------------------- Top 10 Investors -------------------- #
st.subheader("💼 Top 10 Investors")
if 'Investors Name' in df.columns:
    investors = selected_years['Investors Name'].dropna().str.split(',', expand=True).stack()
    top_investors = investors.value_counts().head(10)
    st.bar_chart(top_investors)
else:
    st.warning("'Investors Name' column not found!")

# -------------------- Top Industry Verticals -------------------- #
st.subheader("📊 Top Industry Verticals")
if 'Industry Vertical' in df.columns:
    top_industries = selected_years['Industry Vertical'].value_counts().head(10)
    st.bar_chart(top_industries)
else:
    st.warning("'Industry Vertical' column not found!")

# -------------------- Optional: Seaborn plots -------------------- #
st.subheader("💹 Funding Trend Line Chart")
plt.figure(figsize=(12,6))
sns.lineplot(data=yearwise.reset_index(), x='Date', y='Amount in USD', marker='o')
plt.xticks(rotation=45)
plt.ylabel("Funding Amount (USD)")
plt.xlabel("Year")
plt.grid(True)
st.pyplot(plt)
