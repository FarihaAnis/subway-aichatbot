import os
import requests
import json
from dotenv import load_dotenv

# ✅ Load API key from .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# ✅ Local cache file to store API results
CACHE_FILE = "geocode_cache.json"

# ✅ Load existing cache
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as file:
        geocode_cache = json.load(file)
else:
    geocode_cache = {}

def get_coordinates(address):
    """Fetch latitude and longitude for a given address using Google Maps API, with caching."""
    
    # ✅ Check if address is already in cache
    if address in geocode_cache:
        print(f"🔹 Using cached data for: {address}")
        return geocode_cache[address]["lat"], geocode_cache[address]["lng"]

    # ✅ If not in cache, make API request
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": API_KEY}

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            
            # ✅ Store result in cache
            geocode_cache[address] = location
            with open(CACHE_FILE, "w") as file:
                json.dump(geocode_cache, file)

            return location["lat"], location["lng"]
        else:
            print(f"❌ API Error: {data['status']}")
            return None, None

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching coordinates: {e}")
        return None, None

# ✅ Example usage
if __name__ == "__main__":
    address = "1600 Amphitheatre Parkway, Mountain View, CA"
    latitude, longitude = get_coordinates(address)

    if latitude and longitude:
        print(f"📍 Coordinates: {latitude}, {longitude}")
    else:
        print("❌ Could not fetch coordinates.")
