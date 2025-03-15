## MySQL Database Setup Guide
1. **Setup MySQL Database** (Not included in any Python file—this step is done in MySQL)
   - Create a database named `subway_db` in MySQL
2. **Configure SQLAlchemy Connection (`database.py`)**
   - Define the database connection string in Python:
     ```python
     DB_URL = "mysql+mysqlconnector://username:password@localhost:3306/subway_db"
     ```
   - This sets up the connection to MySQL using SQLAlchemy
3. **Define the Subway Outlet model (`database.py`)**
   - Create a schema to store Subway outlet details
   - This defines the table structure for storing Subway outlet information
4. **Create database table `subway_outlets` (`database.py`)**
   - Run `Base.metadata.create_all(bind=engine)`
   - This creates the `subway_outlets` table in MySQL based on the defined model
5. **Define API Schemas (`schemas.py`)**
   - Create `SubwayOutletSchema` → Defines the API response schema for retrieving Subway outlet data from the database
   - Create `ChatbotRequest` → Defines the chatbot query schema for receiving user queries through the API

---

## Weaviate Database Setup Guide
1. **Log in to Weaviate Cloud**
2. **Create a New Weaviate Cluster**
   - Go to Clusters and create a sandbox named `subway`.
   - Copy the REST API endpoint and save it as `WEAVIATE_URL` in the `.env` file.
   - Copy the API key and save it as `WEAVIATE_API_KEY` in the `.env` file.
3. **Set Up Collections**
   - Go to Collections and create a new collection.
   - Fill in the General and `SubwayOutlet` schema details.
4. **Create `ingest_data.py`**
   - This script will handle data ingestion from MySQL to Weaviate.
5. **Load API Keys from `.env`**
   - Use `load_dotenv()` to load environment variables.
   - Access `WEAVIATE_API_KEY` with `os.getenv("WEAVIATE_API_KEY")`.
6. **Initialize Weaviate Client**
   - Connect to the Weaviate cloud instance using `weaviate.connect_to_weaviate_cloud()`.
   - Authenticate with `AuthApiKey(WEAVIATE_API_KEY)`.
7. **Fetch Data From MySQL**
   - Establish a database session with `SessionLocal()`.
   - Retrieve all Subway outlet records from MySQL.

---

## Web Scraping Workflow
1. **Create `scraping.py` file**
2. **Configure MySQL Database Connection**
   - Connect to MySQL using SQLAlchemy.
   - Use a session to insert or update scraped data.
3. **Set Up Web Scraper**
   - Use Selenium to interact with the Subway website.
   - Uses `webdriver.Chrome()` to launch a Chrome browser controlled by Selenium.
   - Configure with `ChromeOptions()` for headless browsing to run the scraper in the background without opening a browser window. 
   - Set the correct user-agent to avoid detection.
   - To check your current user-agent, visit: [Detect User Agent](https://www.whatismybrowser.com/detect/what-is-my-user-agent)
4. **Load the Subway Website**
   - Navigate to the "Find a Subway" page using `driver.get(BASE_URL)`.
   - Allow time for JavaScript to fully load before scraping.
5. **Search for "Kuala Lumpur" Outlets**
   - Locate the search box and enter "Kuala Lumpur".
   - Click the search button only when it becomes clickable.
   - Wait until the search results appear before extracting data.
6. **Inspect the HTML Structure**
   - Use "View Page Source" or Developer Tools (Inspect Element) to identify where the data is stored.
   - Locate container `<div>` tags, headers `<h4>`, and paragraphs `<p>` that hold outlet details.
7. **Extract Outlet Details**
   - Define `extract_data(page_soup)` function to extract name, address, operating hours, latitude, longitude, and Waze link from the page.
   - Use BeautifulSoup to to find and process these elements in the HTML.
   - Extract text and clean the data by removing unnecessary whitespace and redundant content.
   - Filter only Kuala Lumpur locations by checking if "kuala lumpur" is in the address.
8. **Handle Pagination**
   - Create a while loop to check for pagination. In HTML, the button is typically an <a> (anchor) tag with a class name like "next-page".
   - WebdriverWait waits until the "Next Page" button appears before proceeding.
   - If the button exists, Selenium clicks it and moves to the next page.
   - If the button does not exist, the loop breaks (stops scraping).
9. **Store Data in MySQL**
   - Before inserting, run SQL query (SELECT COUNT(*)) to check if the outlet with the same name and address is already stored.
   - If new → Run `INSERT INTO subway_outlets`to insert the record.
   - If existing → Run `UPDATE subway_outlets`to update details such as operating hours etc.
   - Commit the changes using session.commit() after every insert or update.
10. **Close Browser After Scraping**
    - Use `driver.quit()` to completely close the browser.
11. **Verify Data**
    - Open MySQL database and check the inserted/updated data.
    - Ensure the format is correct and there are no missing values.

---

## Geocoding (`geocoding.py`)
1. **Load Google Maps API key from `.env` file**
2. **Use Local Cache for Stored Coordinates**
   - A cache file stores previously retrieved geolocation data in JSON format to reduce API calls, improves efficiency, and saves API quota.
   - If the requested address already exists in the cache, the stored coordinates are used instead of making a new API request.
   - If you ever want to clear the cache and force API calls again, just delete geocode_cache.json.
3. **Define `get_coordinates` Function**
   - Define the function to fetch latitude and longitude for a given address.
   - Before making an API request, the function checks if the address is in the cache.
4. **Request Coordinates from Google Maps API**
   - If the address is not in the cache, a GET request is sent to the Google Maps API.
   - The API returns location details, including latitude and longitude.
5. **Import `get_coordinates` Function into `scraping.py`**
   - Import geocoding function into the scraping.py to integrate location retrieval with web scraping.
6. **Update `extract_data` Function in `scraping.py`**
   - Modify the `extract_data` function to call `get_coordinates(address)` after extracting each outlet’s name and address.
   - Add the retrieved latitude and longitude to the stored data before inserting into the database.
7. **Update Database Insertion/Update Logic**
   - Adds latitude and longitude to the `INSERT INTO` statement when inserting a new Subway outlet.
   - Updates latitude and longitude in the `UPDATE` query if the outlet already exists.

---

## Backend Setup Guide
1. **Create `app.py`.**
2. **Import FastAPI and initialize the app to manage Subway outlet requests.**
3. **Enable CORS middleware to allow frontend applications to interact with the API**

### Map Visualization Backend
4. **Connect to MySQL Using SQLAlchemy**
5. **Fetching Subway Outlet Data for Map Visualization**
   - Create API endpoint (`GET /outlets`) to retrieve all Subway outlets.
   - Define `get_all_outlets()` function to query the subway_outlets table in MySQL.

### Chatbot Backend
6. **Integrate Weaviate**
   - Load environment variables (Weaviate API Key, Cloud URL) from .env.
   - Initialize Weaviate Client 
      - Connects to Weaviate Cloud to perform hybrid search (semantic + keyword search). 
7. **Fetching Subway outlets data from Weaviate database to handle chatbot queries**
   - Define `retrieve_relevant_outlets()` to perform hybrid search using:
      - vector search (70%)
      - keyword search (30%)
   - Define `convert_to_24_hour()` to convert 12-hour format into 24-hour format for better time sorting.
   - Define `extract_closing_time()` to retrieve the latest closing time from Subway outlets’ operating hours.
   - Define `handle_count_query()` to filter Subway outlets based on location in user queries and return the count.
8. **Processing Chatbot Queries**
   - Define `query_openrouter_llama()`.
      -  Handles general user queries that do not have predefined logic and require Llama-3 (OpenRouter API) to generate responses.
   - Create API endpoint (`POST /chatbot`).
      - Handles user queries and decides whether to return a structured response or use Llama-3 to generate a response.
9. **Closing Weaviate Client on Shutdown**
10. **Run using:**
    ```sh
    uvicorn app:app --reload
    ```

<p align="center"><b>Query Processing Workflow For Retrieving and Responding To User Queries</b></p>
<p align="center">
  <img src="chatbot-workflow.png" alt="Chatbot Workflow">
</p>


