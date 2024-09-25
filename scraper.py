import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import math
import time

# Define scraper function
def scrape_page(url, driver):
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "property-card-module_property-card__wrapper__ZZTal ")))
    
    listings = driver.find_elements(By.CLASS_NAME, "property-card-module_property-card__wrapper__ZZTal ")
    return [{'url': url, 'html_content': listing.get_attribute('outerHTML')} for listing in listings]

# Extract data from HTML
def extract_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    property_type_elem = soup.find('p', class_='styles-module_content__property-type__QuVl4')
    price_elem = soup.find('p', class_='styles-module_content__price__SgQ5p')
    title_elem = soup.find('h2', class_='styles-module_content__title__eOEkd')
    broker_logo_elem = soup.find('div', class_='styles-module_content__broker-logo__6-u-9')
    location_elem = soup.find('div', class_='styles-module_content__location-container__pRGhf')
    bedrooms_elem = soup.find('p', {'data-testid': 'property-card-spec-bedroom'})
    bathrooms_elem = soup.find('p', {'data-testid': 'property-card-spec-bathroom'})
    area_elem = soup.find('p', {'data-testid': 'property-card-spec-area'})
    
    property_type = property_type_elem.text.strip() if property_type_elem else None
    price = price_elem.text.strip() if price_elem else None
    title = title_elem.text.strip() if title_elem else None
    broker_logo_url = broker_logo_elem.find('img')['src'] if broker_logo_elem else None
    location = location_elem.find('p').text.strip() if location_elem else None
    bedrooms = bedrooms_elem.text.strip() if bedrooms_elem else None
    bathrooms = bathrooms_elem.text.strip() if bathrooms_elem else None
    area = area_elem.text.strip() if area_elem else None
    
    return property_type, price, title, broker_logo_url, location, bedrooms, bathrooms, area

# Streamlit app starts here
def main():
    st.title("PropertyFinder Scraper")

    # Password authentication
    password = st.text_input("Enter Password:", type="password")
    if password != "1234":
        st.warning("Incorrect password.")
        st.stop()

    # Input total number of listings
    total_listings = st.number_input("Enter total number of expected listings:", min_value=1, step=1)

    # User inputs PropertyFinder URL
    url = st.text_input("Enter PropertyFinder URL:")

    # Add button to stop the scraping process
    if "stop_scraping" not in st.session_state:
        st.session_state.stop_scraping = False  # Initialize the stop flag


    if st.button("Scrape Data"):
        
        if url:
            # Calculate number of pages to scrape (assuming 25 listings per page)
            n = math.ceil(total_listings / 25)
            
            # Initialize WebDriver in headless mode
            driver = webdriver.Chrome()
            
            all_listings = []

            try:
                st.info(f"Scraping {n} pages... This may take a while.")
                placeholder = st.empty()
                for i in range(1, n + 1):
                    
                    paginated_url = f"{url}&page={i}"
                    percentage = (i / n) * 100
                    placeholder.text(f"Scraping page {i} of {n}: {percentage:.2f}%")  # Progress output
                    
                    listings = scrape_page(paginated_url, driver)
                    all_listings.extend(listings)
                    time.sleep(0.1)  # Small delay between requests

                driver.quit()

                if all_listings:
                    # Extract data and save to DataFrame
                    df = pd.DataFrame(all_listings)
                    df['property_type'], df['price'], df['title'], df['broker_logo_url'], df['location'], df['bedrooms'], df['bathrooms'], df['area'] = \
                        zip(*df['html_content'].apply(extract_data))

                    # Allow user to download the CSV file
                    csv = df.to_csv(index=False)
                    st.success("Scraping completed successfully!")
                    st.download_button("Download CSV", csv, "results.csv", "text/csv")
                else:
                    st.warning("No data to export. Scraping did not collect any listings.")

            except Exception as e:
                st.error(f"Error occurred: {e}")
                driver.quit()
        else:
            st.warning("Please enter a valid PropertyFinder URL.")


if __name__ == "__main__":
    main()
