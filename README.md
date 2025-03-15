# Subway Outlet Data Pipeline

## Initialize Git Repo
1. Create repo in GitHub
2. In cmd navigate to the working folder 
3. Initialize Git (`git init`)

---

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
   - Configure with `ChromeOptions()` for headless browsing to run the scraper in the background.
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
   - Use "View Page Source" or Developer Tools to locate data elements.
7. **Extract Outlet Details**
   - Define `extract_data(page_soup)` function to extract details.
   - Use BeautifulSoup to find elements and clean extracted text.
   - Filter only Kuala Lumpur locations.
8. **Handle Pagination**
   - Use a `while` loop to navigate pages.
   - If a "Next Page" button exists, Selenium clicks it.
   - If the button does not exist, the loop stops.
9. **Store Data in MySQL**
   - Check if the outlet already exists.
   - If new → Run `INSERT INTO subway_outlets`.
   - If existing → Run `UPDATE subway_outlets`.
   - Commit the changes using `session.commit()`.
10. **Close Browser After Scraping**
    - Use `driver.quit()` to completely close the browser.
11. **Verify Data**
    - Open MySQL database and check the inserted/updated data.

---

## Geocoding (`geocoding.py`)
1. **Load Google Maps API key from `.env` file**
2. **Use Local Cache for Stored Coordinates**
   - A cache file stores previously retrieved geolocation data in JSON format.
   - If the requested address exists in the cache, stored coordinates are used.
3. **Define `get_coordinates` Function**
   - Fetches latitude and longitude for a given address.
   - If not found, retrieves data from Google Maps API.
4. **Handle Errors**
   - If API request fails, return `None`.
5. **Import `get_coordinates` Function into `scraping.py`**
6. **Update `extract_data` Function in `scraping.py`**
   - Modify the function to call `get_coordinates(address)`.
7. **Update Database Insertion/Update Logic**
   - Add latitude and longitude fields.

---

## Backend Setup
1. **Create `app.py`**
2. **Import FastAPI and initialize the app**
3. **Enable CORS middleware**

### Map Visualization Backend
4. **Connect to MySQL Using SQLAlchemy**
5. **Fetching Subway Outlet Data for Map Visualization**
   - Create API endpoint (`GET /outlets`)
   - Define `get_all_outlets()` function.

### Chatbot Backend
6. **Integrate Weaviate**
7. **Fetching Subway Outlet Data from Weaviate**
   - Define `retrieve_relevant_outlets()`.
8. **Processing Chatbot Queries**
   - Define `query_openrouter_llama()`.
   - Create API endpoint (`POST /chatbot`).
9. **Closing Weaviate Client on Shutdown**
10. **Run using:**
    ```sh
    uvicorn app:app --reload
    ```

---

## Frontend Setup
1. **Create a `frontend` folder**
2. **Initialize a React App inside the folder:**
   ```sh
   npx create-react-app .
   ```
3. **Place necessary images inside the `public` folder**

### Implementation of Frontend Code
4. **Open `App.js`**
5. **Import required modules**
6. **Map Visualization Setup**
7. **Fetch Subway Outlet Data from FastAPI**
8. **Chatbot UI Setup**
9. **Update UI Styling in `App.css`**
