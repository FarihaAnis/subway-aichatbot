from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, SubwayOutlet
from schemas import ChatbotRequest, SubwayOutletSchema
import weaviate
import weaviate.classes as wvc
import os
from dotenv import load_dotenv
import requests
import logging
from typing import List
from fastapi.responses import JSONResponse
import re
from datetime import datetime

# ✅ Load environment variables
load_dotenv()

# ✅ Weaviate Configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # OpenRouter API key for Llama-3

# ✅ Initialize FastAPI
app = FastAPI()

# ✅ Allow frontend requests (Fix CORS policy)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Set up logging
logging.basicConfig(level=logging.INFO)

# ✅ Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Subway Outlet API Endpoints
@app.get("/outlets", response_model=List[SubwayOutletSchema])
def get_all_outlets(db: Session = Depends(get_db)):
    outlets = db.query(SubwayOutlet).all()
    if not outlets:
        raise HTTPException(status_code=404, detail="No Subway outlets found")
    return outlets

# @app.get("/outlets/{outlet_id}", response_model=SubwayOutletSchema)
# def get_outlet(outlet_id: int, db: Session = Depends(get_db)):
#     outlet = db.query(SubwayOutlet).filter(SubwayOutlet.id == outlet_id).first()
#     if not outlet:
#         raise HTTPException(status_code=404, detail="Outlet not found")
#     return outlet

# ✅ Initialize Weaviate Client with Authentication
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,
    auth_credentials=wvc.init.Auth.api_key(WEAVIATE_API_KEY),
)

# ✅ Check if Weaviate is accessible
try:
    client.is_ready()
    logging.info("✅ Successfully connected to Weaviate!")
except Exception as e:
    logging.error(f"❌ Weaviate connection failed: {str(e)}", exc_info=True)
    raise RuntimeError("Weaviate is not reachable. Ensure it's running and API key is correct.")

# ✅ Convert Time to 24-Hour Format for Proper Sorting
def convert_to_24_hour(time_str):
    try:
        return datetime.strptime(time_str, "%I:%M %p").time()
    except ValueError:
        return None  # Return None if conversion fails
# Mapping short-form days to full names for better interpretation
day_mapping = {
    "Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday",
    "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday", "PH": "Public Holiday"
}

def extract_closing_time(hours_text):
    """
    Extracts the latest closing time from Subway operating hours.
    Handles:
    - Short-form days (e.g., "Mon - Sun")
    - Full-form days (e.g., "Monday - Sunday")
    - Multiple closing times
    - Public holiday closing times
    """
    try:
        # Normalize text (replace en-dash with hyphen, fix spaces)
        hours_text = re.sub(r"–", "-", hours_text)  # Convert en-dash to hyphen
        hours_text = re.sub(r"\s+", " ", hours_text).strip()  # Normalize spaces
        
        # Convert short-form days (Mon-Sun) to full names
        for short, full in day_mapping.items():
            hours_text = re.sub(rf"\b{short}\b", full, hours_text)  # Replace short day names
        
        # Extract time entries (e.g., "8:00 AM", "10:30 PM")
        time_patterns = re.findall(r"(\d{1,2}:\d{2}\s?[APMapm]{2})", hours_text)

        if not time_patterns:
            return None, None  # No valid time format found

        closing_times = []
        public_holiday_times = []

        # Identify public holiday times separately
        is_public_holiday = "public holiday" in hours_text.lower()

        for time_str in time_patterns:
            try:
                closing_time = datetime.strptime(time_str.strip(), "%I:%M %p").time()

                if is_public_holiday:
                    public_holiday_times.append(closing_time)
                else:
                    closing_times.append(closing_time)
            except ValueError:
                continue  # Skip invalid formats

        normal_latest = max(closing_times) if closing_times else None
        holiday_latest = max(public_holiday_times) if public_holiday_times else None
        
        return normal_latest, holiday_latest

    except Exception as e:
        print(f"❌ Error parsing operating hours: {str(e)}")
        return None, None  # Return None on error


# ✅ Hybrid Search Function (Vector + Keyword Search + Filtering)
def retrieve_relevant_outlets(query_text, alpha=0.7, limit=100):
    """
    Performs Hybrid Search in Weaviate.
    - `alpha=0.7` → 70% Vector Search, 30% Keyword Search
    """
    try:
        subway_outlets = client.collections.get("SubwayOutlet")

        response = subway_outlets.query.hybrid(
            query=query_text,
            alpha=alpha,
            return_metadata=wvc.query.MetadataQuery(score=False),  # ✅ Score removed
            limit=limit
        )

        return response.objects if response.objects else []  # Return relevant objects

    except Exception as e:
        logging.error(f"❌ Error querying Weaviate: {str(e)}", exc_info=True)
        return []

# ✅ Chatbot Endpoint using Llama 3 (OpenRouter API)
def query_openrouter_llama(prompt):
    """
    Calls OpenRouter API with Llama 3.3 70B Instruct.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "prompt": prompt,
        "max_tokens": 1000,
        "temperature": 0.1,
        "stop": ["User Query:"]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json().get("choices", [{}])[0].get("text", "No response received.")

        logging.error(f"❌ OpenRouter API Error: {response.status_code}, {response.text}")
        return f"Error: {response.status_code}, {response.text}"

    except Exception as e:
        logging.error(f"❌ Failed to connect to OpenRouter API: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"

def handle_count_query(query, relevant_outlets):
    """
    Handles queries that ask for a count of Subway outlets.
    Dynamically filters locations based on exact phrase matching in addresses.
    """
    location_match = re.search(r"in ([\w\s]+)", query, re.IGNORECASE)
    location_filter = location_match.group(1).strip().lower() if location_match else None

    def is_exact_location_match(address, location_filter):
        """
        Returns True if the full location phrase matches anywhere in the address.
        Fixes the issue with multi-word locations like 'Kuala Lumpur'.
        """
        if not address:
            return False

        address = address.lower()
        location_filter = location_filter.lower()

        # ✅ Direct phrase matching instead of word splitting
        return location_filter in address  

    if location_filter:
        filtered_outlets = [
            outlet for outlet in relevant_outlets
            if is_exact_location_match(outlet.properties.get('address', ''), location_filter)
        ]
    else:
        filtered_outlets = relevant_outlets  # No specific location in query

    total_count = len(filtered_outlets)

    if total_count == 0:
        return {"response": f"<p>❌ There are no Subway outlets matching your search.</p>"}

    # ✅ Only return outlet names and count
    outlet_names = [outlet.properties.get('name', 'Unknown') for outlet in filtered_outlets]

    # ✅ Handle singular/plural wording
    if total_count == 1:
        response_text = f"""
        <p>There is <b>1</b> Subway outlet in <b>{location_filter.title()}</b>, 
        located at <b>{outlet_names[0]}</b>.</p>
        """
    else:
        response_text = f"""
        <p>There are <b>{total_count}</b> Subway outlets in <b>{location_filter.title()}</b>, located at:</p>
        <ul>
            {''.join(f'<li>🏪 <b>{name}</b></li>' for name in outlet_names)}
        </ul>
        """
    return {"response": response_text}

@app.post("/chatbot")
def chatbot_query(request: ChatbotRequest):
    """
    Process user queries using Hybrid Search & OpenRouter's Llama-3.
    """
    try:
        query = request.query.strip().lower()
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        logging.info(f"🔍 Received query: {query}")

        # ✅ Retrieve hybrid search results
        relevant_outlets = retrieve_relevant_outlets(query) # determines whether to return structured data or call Llama-3 for a natural language response

        # ✅ Handle count-based queries FIRST
        if "count" in query or "many" in query:
            logging.info(f"🔍 Handling count query: {query}")
            response = handle_count_query(query, relevant_outlets)
            logging.info(f"📝 Response from handle_count_query: {response}")
            return handle_count_query(query, relevant_outlets)

        # ✅ Handle "closes the latest" queries
        if "closes the latest" in query or "open the longest" in query:
            logging.info("🔍 Handling latest closing time query")
            closing_times = []

            for outlet in relevant_outlets:
                operating_hours = outlet.properties.get("operating_hours", "")
                normal_closing, holiday_closing = extract_closing_time(operating_hours)

                if normal_closing:
                    closing_times.append((outlet, normal_closing, holiday_closing))

            if closing_times:
                # ✅ Find the latest closing outlet
                latest_closing_time = max(closing_times, key=lambda x: x[1])[1]
                latest_outlets = [
                    (outlet, normal_closing, holiday_closing)
                    for outlet, normal_closing, holiday_closing in closing_times
                    if normal_closing == latest_closing_time
                ]

                response_list = []
                for outlet, normal_closing, holiday_closing in latest_outlets:
                    name = outlet.properties.get('name', 'Unknown')
                    address = outlet.properties.get('address', 'Not available')
                    operating_hours = outlet.properties.get('operating_hours', 'N/A')
                    latitude = outlet.properties.get('latitude', 'N/A')
                    longitude = outlet.properties.get('longitude', 'N/A')
                    waze_link = outlet.properties.get('waze_link', '').strip()

                    # ✅ Ensure Waze link is correctly formatted
                    waze_text = (
                        f'<a href="{waze_link}" target="_blank" rel="noopener noreferrer" '
                        f'style="color: #007bff; text-decoration: none;">🚗 Navigate Here</a>'
                    ) if waze_link and waze_link not in ['#', '', None, 'None'] else "No Waze link available"

                    response_list.append(
                        f"<b>{name}</b><br>"
                        f"📍 Address: {address}<br>"
                        f"🕒 Operating Hours: {operating_hours}<br>"
                        f"🚦 Public Holiday Status: {'Closed' if holiday_closing else 'Open'}<br>"
                        f"🌍 Location: Latitude {latitude}, Longitude {longitude}<br>"
                        f"{waze_text}<br>"
                    )

                return {"response": f"The latest closing Subway outlet(s): <br>{'<br>'.join(response_list)}"}

        # ✅ General Responses (For queries that do not match count/latest closing queries)
        formatted_outlets = []
        outlet_names = []

        for outlet in relevant_outlets:
            name = outlet.properties.get('name', 'Unknown')
            address = outlet.properties.get('address', 'Not available')
            operating_hours = outlet.properties.get('operating_hours', 'Not available')
            latitude = outlet.properties.get('latitude', 'N/A')
            longitude = outlet.properties.get('longitude', 'N/A')
            waze_link = outlet.properties.get('waze_link', '')

            # ✅ Ensure Waze link is properly formatted and clickable
            waze_text = (
                f'<a href="{waze_link.strip()}" target="_blank" rel="noopener noreferrer" '
                f'style="color: #007bff; text-decoration: none;">🚗 Navigate Here</a>'
            ) if waze_link and waze_link.strip() not in ["#", "", None, "None"] else "No Waze link available"

            outlet_names.append(name)
            formatted_outlets.append(
                f"<b>{name}</b><br>"
                f"📍 Address: {address}<br>"
                f"🕒 Operating Hours: {operating_hours}<br>"
                f"🌍 Latitude: {latitude}, Longitude: {longitude}<br>"
                f"{waze_text}<br>"
            )

        response_context = "".join(formatted_outlets)

        # ✅ Construct the final prompt dynamically
        full_prompt = f"""
        ### Context:
        You are an AI assistant helping users find Subway outlets with specific queries.

        ### Query:
        The user wants to know about Subway outlets that {query}. 

        ### Retrieved Data:
        {response_context}
        
        ### Final Answer:
        """

        response = query_openrouter_llama(full_prompt)
        logging.info(f"🔍 Received response from Llama 3: {response}")

        return {"response": response.strip()}

    except Exception as e:
        logging.error(f"❌ ERROR: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal Server Error", "message": str(e)})

# ✅ Close Weaviate Client on Shutdown
@app.on_event("shutdown")
def shutdown():
    client.close()
    logging.info("✅ Weaviate client connection closed.")
