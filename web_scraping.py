import logging
from pathlib import Path

import pandas as pd
from selenium import webdriver as wd
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

RAW_CSV = Path("weather_raw.csv")
CLEAN_CSV = Path("weather_clean.csv")
URL = "https://www.timeanddate.com/weather"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def build_driver():
    service = Service(ChromeDriverManager().install())
    return wd.Chrome(service=service)


def load_page(driver, url):
    driver.get(url)
    
    # Wait for the page body to load
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


def clean_data(data):
    df = pd.DataFrame(data)
    if df.empty:
        return df

    df = df.dropna().drop_duplicates().reset_index(drop=True)
    df["City"] = df["City"].str.strip()
    df["Temperature"] = df["Temperature"].str.replace(r"[^0-9+\-.]", "", regex=True)
    df["Local Time"] = df["Local Time"].str.strip()
    return df


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

    pd.DataFrame(data).to_csv(RAW_CSV, index=False)
    clean_data(data).to_csv(CLEAN_CSV, index=False)
    logging.info("Saved raw and cleaned CSV files.")
    logging.info("Scraping finished with %d rows saved.", len(data))


if __name__ == "__main__":
    main()


