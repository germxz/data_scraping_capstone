import pandas as pd
import sqlite3

# Load CSVs into DataFrames
raw_df = pd.read_csv('weather_raw.csv')
clean_df = pd.read_csv('weather_clean.csv')

# Show before/after
print("RAW DATA:")
print(raw_df.head())
print("\nCLEAN DATA:")
print(clean_df.head())

try:
    with sqlite3.connect('./db/weather.db') as conn:
        # Load raw data into database
        raw_df.to_sql('weather_raw', conn, if_exists='replace', index=False)
        
        # Load clean data into database
        clean_df.to_sql('weather_clean', conn, if_exists='replace', index=False)
        
        print("\nData successfully saved to weather.db")

except sqlite3.Error as e:
    print(f"An error occurred: {e}")