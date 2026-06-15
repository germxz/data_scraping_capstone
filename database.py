import pandas as pd
import sqlite3

# Load CSVs into DataFrames
raw_df = pd.read_csv('weather_raw.csv')
clean_df = pd.read_csv('weather_clean.csv')

# Show before/after
print("=" * 60)
print("BEFORE CLEANING (Raw Data):")
print("=" * 60)
print(raw_df.head(10))
print(f"\nShape: {raw_df.shape}")
print(f"Missing values:\n{raw_df.isnull().sum()}")

print("\n" + "=" * 60)
print("AFTER CLEANING (Clean Data):")
print("=" * 60)
print(clean_df.head(10))
print(f"\nShape: {clean_df.shape}")
print(f"Missing values:\n{clean_df.isnull().sum()}")

print("\n" + "=" * 60)
print("TRANSFORMATIONS APPLIED:")
print("=" * 60)
print(f"Rows removed by cleaning: {len(raw_df) - len(clean_df)}")
print("Standardized temperature format (numeric)")
print("Stripped whitespace from text fields")
print("Removed duplicate records")

try:
    with sqlite3.connect('./db/weather.db') as conn:
        # Load raw data into database
        raw_df.to_sql('weather_raw', conn, if_exists='replace', index=False)
        
        # Load clean data into database
        clean_df.to_sql('weather_clean', conn, if_exists='replace', index=False)
        
        print("\n✓ Data successfully saved to ./db/weather.db")
        print(f"  - weather_raw table: {len(raw_df)} rows")
        print(f"  - weather_clean table: {len(clean_df)} rows")

except sqlite3.Error as e:
    print(f"An error occurred: {e}")