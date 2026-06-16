"""Interactive dashboard for weather data visualization."""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Path to the SQLite database created by database.py
DATABASE_FILE = Path("db/weather.db")

# Streamlit page configuration
st.set_page_config(
    page_title="Weather Dashboard",
    page_icon="🌍",
    layout="wide",
)


def load_data_from_db(db_path: Path) -> pd.DataFrame:
    """Load weather data from SQLite database."""
    # Connect to the database
    with sqlite3.connect(db_path) as conn:
        # Read the weather table into a pandas DataFrame
        df = pd.read_sql_query("SELECT * FROM weather_clean", conn)
    return df


# Load the data from the database
if not DATABASE_FILE.exists():
    st.error(f"Database file not found: {DATABASE_FILE}")
    st.info("Please run save_to_sqlite.py first to create the database.")
    st.stop()

# Load weather data into a DataFrame
weather_df = load_data_from_db(DATABASE_FILE)

# Display the main title
st.title("🌍 Weather Around The World Dashboard")

# Show a summary of the data
st.markdown("---")
st.subheader("📊 Data Summary")

# Display basic statistics about the dataset
col1, col2, col3 = st.columns(3)
col1.metric("Total Cities", len(weather_df))
col2.metric("Average Temperature", f"{weather_df['Temperature'].mean():.1f}°F")
col3.metric("Temperature Range", f"{weather_df['Temperature'].min()}°F - {weather_df['Temperature'].max()}°F")

# Display the raw data table
st.markdown("---")
st.subheader("📋 Raw Data Table")

# Allow user to filter by temperature range
temp_min, temp_max = st.slider(
    "Filter by temperature range (°F):",
    int(weather_df['Temperature'].min()),
    int(weather_df['Temperature'].max()),
    (int(weather_df['Temperature'].min()), int(weather_df['Temperature'].max()))
)

# Filter the data based on the slider
filtered_df = weather_df[
    (weather_df['Temperature'] >= temp_min) & 
    (weather_df['Temperature'] <= temp_max)
]

# Display the filtered data table
st.dataframe(filtered_df, use_container_width=True)

# Display visualizations
st.markdown("---")
st.subheader("📈 Visualizations")

# Visualization 1: Temperature Distribution Histogram
st.markdown("### Visualization 1: Temperature Distribution")
fig_hist = px.histogram(
    weather_df,
    x='Temperature',
    nbins=15,
    title="Distribution of Temperatures Across Cities",
    labels={'Temperature': 'Temperature (°F)', 'count': 'Number of Cities'},
    color_discrete_sequence=['#1f77b4']
)
st.plotly_chart(fig_hist, use_container_width=True)

# Visualization 2: Top 15 Warmest Cities
st.markdown("### Visualization 2: Top 15 Warmest Cities")
top_warm = weather_df.nlargest(15, 'Temperature')
fig_warm = px.bar(
    top_warm,
    x='City',
    y='Temperature',
    title="Top 15 Warmest Cities",
    labels={'Temperature': 'Temperature (°F)', 'City': 'City Name'},
    color='Temperature',
    color_continuous_scale='Reds'
)
fig_warm.update_xaxes(tickangle=-45)
st.plotly_chart(fig_warm, use_container_width=True)

# Visualization 3: Top 15 Coldest Cities
st.markdown("### Visualization 3: Top 15 Coldest Cities")
top_cold = weather_df.nsmallest(15, 'Temperature')
fig_cold = px.bar(
    top_cold,
    x='City',
    y='Temperature',
    title="Top 15 Coldest Cities",
    labels={'Temperature': 'Temperature (°F)', 'City': 'City Name'},
    color='Temperature',
    color_continuous_scale='Blues'
)
fig_cold.update_xaxes(tickangle=-45)
st.plotly_chart(fig_cold, use_container_width=True)

# Visualization 4: Temperature by Time Zone (first character of Local Time)
st.markdown("### Visualization 4: Temperature Statistics by Time")
# Extract hour from Local Time string (e.g., "3:45 am" -> "3 am")
weather_df['Time Period'] = weather_df['Local Time'].str.extract(r'(\d+\s?(?:am|pm))', expand=False)

fig_box = px.box(
    weather_df,
    x='Time Period',
    y='Temperature',
    title="Temperature Distribution by Local Time Period",
    labels={'Temperature': 'Temperature (°F)', 'Time Period': 'Local Time'},
    color_discrete_sequence=['#2ca02c']
)
st.plotly_chart(fig_box, use_container_width=True)

# Interactive city search
st.markdown("---")
st.subheader("🔍 Search Specific City")

# Create a dropdown to select a city
selected_city = st.selectbox(
    "Select a city to view details:",
    sorted(weather_df['City'].unique())
)

# Display details for the selected city
city_data = weather_df[weather_df['City'] == selected_city].iloc[0]
col1, col2, col3 = st.columns(3)
col1.metric("City", city_data['City'])
col2.metric("Temperature", f"{city_data['Temperature']}°F")
col3.metric("Local Time", city_data['Local Time'])

# Display footer
st.markdown("---")
st.markdown(
    """
    **Dashboard Information:**
    - Data source: Weather Around The World (timeanddate.com)
    - Data cleaned and stored in SQLite database
    - Visualizations built with Plotly
    - Interactive dashboard built with Streamlit
    """
)
