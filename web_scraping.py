import logging
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
from selenium import webdriver as wd
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

RAW_CSV = Path("weather_raw.csv")
CLEAN_CSV = Path("weather_clean.csv")
DB_FILE = Path("./db/weather.db")
URL = "https://www.timeanddate.com/weather"

# Day abbreviation -> weekday number, used to handle times that cross midnight
DAYS = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def build_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())
    driver = wd.Chrome(service=service, options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver


def load_page(driver, url):
    driver.get(url)
    input("Complete the Cloudflare check in the browser, then press Enter here to scrape...")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    logging.info("Page loaded successfully.")


def scrape_weather(driver):
    rows = driver.find_elements(By.CSS_SELECTOR, "table.zebra.tb-wt tr")
    if not rows:
        rows = driver.find_elements(By.TAG_NAME, "tr")

    results = []
    for row in rows:
        try:
            city = row.find_element(By.CSS_SELECTOR, "td a").text.strip()
            temp = row.find_element(By.CSS_SELECTOR, "td.rbi").text.strip()
            local_time = row.find_element(By.CSS_SELECTOR, "td.r").text.strip()
        except NoSuchElementException:
            continue
        if city and temp and local_time:
            results.append({"City": city, "Temperature": temp, "Local Time": local_time})

    return results


def hours_from_central(city_time_str, central_now):
    """Whole-hour difference between a city's scraped local time and Central time.

    Approximate: rounds to the nearest hour and assumes the machine running
    this is on Central time (the anchor for the comparison).
    """
    m = re.match(r"(\w{3})\s+(\d{1,2}):(\d{2})\s*(am|pm)", city_time_str.strip(), re.IGNORECASE)
    if not m:
        return None
    day, hh, mm, ap = m.group(1).title(), int(m.group(2)), int(m.group(3)), m.group(4).lower()
    if day not in DAYS:
        return None
    if ap == "pm" and hh != 12:
        hh += 12
    if ap == "am" and hh == 12:
        hh = 0

    city_total = DAYS[day] * 1440 + hh * 60 + mm
    central_total = central_now.weekday() * 1440 + central_now.hour * 60 + central_now.minute
    diff_min = city_total - central_total

    # Wrap into the real-world timezone span (-12h .. +14h)
    while diff_min > 14 * 60:
        diff_min -= 1440
    while diff_min < -12 * 60:
        diff_min += 1440
    return round(diff_min / 60)


def clean_data(df):
    if df.empty:
        return df

    df = df.dropna().drop_duplicates().reset_index(drop=True)
    df["City"] = df["City"].str.strip()
    df["Local Time"] = df["Local Time"].str.strip()
    # Strip units/symbols and convert temperature to a real numeric column
    df["Temperature"] = (
        df["Temperature"]
        .str.replace(r"[^0-9+\-.]", "", regex=True)
        .pipe(pd.to_numeric, errors="coerce")
    )
    df = df.dropna(subset=["Temperature"]).reset_index(drop=True)
    df["Temperature"] = df["Temperature"].astype(int)

    # Hours each city is ahead (+) or behind (-) Central time at scrape moment
    central_now = datetime.now()
    df["Hours From Central"] = df["Local Time"].apply(
        lambda t: hours_from_central(t, central_now)
    )
    return df


def save_to_database(raw_df, clean_df):
    # Save each DataFrame into its own table in a SQLite database
    conn = sqlite3.connect(DB_FILE)
    raw_df.to_sql("weather_raw", conn, if_exists="replace", index=False)
    clean_df.to_sql("weather_clean", conn, if_exists="replace", index=False)
    conn.close()
    logging.info("Saved data to SQLite database: %s", DB_FILE)


def main():
    logging.info("Starting weather scraping for %s", URL)
    driver = build_driver()
    try:
        load_page(driver, URL)
        data = scrape_weather(driver)
    except Exception as exc:
        logging.error("Unable to load page or scrape data: %s", exc)
        return
    finally:
        driver.quit()

    if not data:
        logging.warning("No weather rows were scraped.")
        return

    # Load the raw scraped data into a Pandas DataFrame
    raw_df = pd.DataFrame(data)

    # Before/after cleaning report
    logging.info("RAW: %d rows", raw_df.shape[0])
    logging.info("Raw sample:\n%s", raw_df.head().to_string(index=False))

    clean_df = clean_data(raw_df)

    logging.info(
        "CLEAN: %d rows (removed %d)",
        clean_df.shape[0],
        raw_df.shape[0] - clean_df.shape[0],
    )
    logging.info("Clean sample:\n%s", clean_df.head().to_string(index=False))

    # Save outputs: CSV files and a SQLite database
    raw_df.to_csv(RAW_CSV, index=False)
    clean_df.to_csv(CLEAN_CSV, index=False)
    logging.info("Saved raw and cleaned CSV files.")

    save_to_database(raw_df, clean_df)
    logging.info("Scraping finished with %d rows saved.", len(clean_df))


if __name__ == "__main__":
    main()