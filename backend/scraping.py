import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from sqlalchemy import text
from database import SessionLocal
from geocoding import get_coordinates  

# ✅ Database connection (MySQL)
session = SessionLocal()

# ✅ Set up Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in background (remove for debugging)
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ✅ Load the Website
BASE_URL = "https://subway.com.my/find-a-subway"
driver.get(BASE_URL)
#time.sleep(5)  # Wait for JavaScript to load content

# ✅ Locate the search box and button using correct IDs
search_box = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "fp_searchAddress"))
)
search_box.clear()
search_box.send_keys("kuala lumpur")

# Click the search button
search_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "fp_searchAddressBtn"))
)
search_button.click()

# Wait for search results to load
#time.sleep(5)

# ✅ Extract updated HTML after JavaScript execution
soup = BeautifulSoup(driver.page_source, "html.parser")

# ✅ Web Scraping Function with Debugging
def extract_data(page_soup):
    outlets = []
    direction_buttons = driver.find_elements(By.CLASS_NAME, "directionButton")  # Selenium extracts dynamic content
    info_boxes = driver.find_elements(By.CLASS_NAME, "infoboxcontent")  # Extract dynamically loaded information

    for outlet, button, info_box in zip(page_soup.find_all("div", class_="location_left"), direction_buttons, info_boxes):
        try:
            name = outlet.find("h4").text.strip()
            address = outlet.find("p").text.strip()

            # Ensure only "Kuala Lumpur" locations are extracted
            if "kuala lumpur" not in address.lower():
                continue

            # Extract operating hours using Selenium
            operating_hours = "N/A"
            try:
                raw_html = info_box.get_attribute("innerHTML")
                soup = BeautifulSoup(raw_html, "html.parser")
                
                paragraphs = soup.find_all("p")  # ✅ Extract all <p> elements
                
                # ✅ Remove empty text and "Find out more..."
                filtered_paragraphs = [p.text.strip() for p in paragraphs if p.text.strip() and "Find out more" not in p.text]
                
                # ✅ Separate address and operating hours
                if filtered_paragraphs:
                    address = filtered_paragraphs[0]  # ✅ First <p> is the address
                    
                    # ✅ Process only operating hours (ignore the first paragraph)
                    operating_hours_lines = []
                    for i in range(1, len(filtered_paragraphs)):  # ✅ Start from second paragraph
                        current_line = filtered_paragraphs[i]
                        
                        # ✅ If the previous line contains operating hours, merge it
                        if operating_hours_lines and any(kw in current_line.lower() for kw in ["am", "pm", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
                            operating_hours_lines[-1] += f" {current_line}"  # ✅ Merge line
                        else:
                            operating_hours_lines.append(current_line)  # ✅ Add new line

                    if operating_hours_lines:
                        operating_hours = " ".join(operating_hours_lines)  # ✅ Merge all operating hours

            except Exception as e:
                print(f"❌ Error extracting operating hours for {name}: {e}")

            # ✅ Fetch latitude & longitude using Google Maps API
            latitude, longitude = None, None
            if address:
                latitude, longitude = get_coordinates(address)
                
            # Extract Waze link using Selenium
            waze_link = "N/A"
            links = button.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                if "waze.com" in href:  # Ensure it's a Waze link
                    waze_link = href
                    break

            # ✅ Store data
            outlets.append((name, address, operating_hours, latitude, longitude, waze_link))
        except AttributeError:
            continue
    return outlets


# ✅ Scrape the Subway locations
outlets = extract_data(soup)

# ✅ Handle Pagination
while True:
    next_button = soup.find("a", class_="next-page")
    if next_button:
        next_page_url = next_button["href"]
        driver.get(next_page_url)
        time.sleep(5)  # Wait for JavaScript to load
        soup = BeautifulSoup(driver.page_source, "html.parser")
        outlets.extend(extract_data(soup))
    else:
        break

driver.quit()  # Close the browser

# ✅ Debugging: Print extracted data
#print("Extracted Data:", outlets)

# ✅ Insert or Update Data in MySQL Table
for outlet in outlets:
    name, address, operating_hours, latitude, longitude, waze_link = outlet

    # Check if the record already exists
    check_query = text("SELECT COUNT(*) FROM subway_outlets WHERE name = :name AND address = :address")
    result = session.execute(check_query, {"name": name, "address": address}).scalar()

    if result == 0:
        # If not exists, INSERT
        insert_query = text("""
            INSERT INTO subway_outlets (name, address, operating_hours, latitude, longitude, waze_link)
            VALUES (:name, :address, :operating_hours, :latitude, :longitude, :waze_link)
        """)
        session.execute(insert_query, {
            "name": name, "address": address, "operating_hours": operating_hours,
            "latitude": latitude, "longitude": longitude, "waze_link": waze_link
        })
    else:
        # If exists, UPDATE
        update_query = text("""
            UPDATE subway_outlets 
            SET operating_hours = :operating_hours, latitude = :latitude, longitude = :longitude, waze_link = :waze_link 
            WHERE name = :name AND address = :address
        """)
        session.execute(update_query, {
            "name": name, "address": address, "operating_hours": operating_hours,
            "latitude": latitude, "longitude": longitude, "waze_link": waze_link
        })

    session.commit()  # Commit after each operation

session.close()

print("✅ Data successfully scraped, inserted/updated in MySQL!")
