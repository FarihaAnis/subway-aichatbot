from sqlalchemy.orm import Session
from database import SessionLocal, SubwayOutlet  # Import database connection
import weaviate
from weaviate.auth import AuthApiKey  # ✅ Corrected import
import os
from dotenv import load_dotenv

# ✅ Load API keys
load_dotenv()
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

# ✅ Initialize Weaviate Client (Updated for v4)
client = weaviate.connect_to_weaviate_cloud(
    WEAVIATE_URL,
    auth_credentials=AuthApiKey(WEAVIATE_API_KEY) if WEAVIATE_API_KEY else None
)

# ✅ Check if Weaviate is accessible
try:
    client.is_ready()
except Exception:
    raise RuntimeError("Weaviate is not reachable. Ensure it's running and API key is correct.")

# ✅ Define Collection Name
CLASS_NAME = "SubwayOutlet"

# ✅ Create Collection (if not exists)
def create_collection():
    if not client.collections.exists(CLASS_NAME):  # ✅ Changed from `client.schema.exists()`
        schema = {
            "class": CLASS_NAME,
            "description": "Subway Outlet Locations and Details",
            "vectorizer": "text2vec-weaviate",
            "moduleConfig": {
                "text2vec-weaviate": {"vectorizeClassName": False}
            },
            "properties": [
                {"name": "name", "dataType": ["string"], "description": "Outlet name"},
                {"name": "address", "dataType": ["string"], "description": "Street address"},
                {"name": "operating_hours", "dataType": ["string"], "description": "Operating hours"},
                {"name": "waze_link", "dataType": ["string"], "description": "Navigation link"},
                {"name": "latitude", "dataType": ["number"], "description": "GPS Latitude"},
                {"name": "longitude", "dataType": ["number"], "description": "GPS Longitude"},
            ]
        }
        client.collections.create(schema)  # ✅ Updated method for v4
        print("✅ Collection 'SubwayOutlet' created in Weaviate.")
    else:
        print("✅ Collection 'SubwayOutlet' already exists.")

# ✅ Ingest Data into Weaviate
def ingest_data():
    create_collection()  # Ensure schema exists before ingestion

    with SessionLocal() as db:
        outlets = db.query(SubwayOutlet).all()
        if not outlets:
            print("⚠️ No Subway outlets found in MySQL database.")
            return
        
        with client.batch.fixed_size(batch_size=10) as batch:  # ✅ Updated for v4
            for outlet in outlets:
                obj = {
                    "name": outlet.name,
                    "address": outlet.address,
                    "operating_hours": outlet.operating_hours,
                    "waze_link": outlet.waze_link,
                    "latitude": outlet.latitude,
                    "longitude": outlet.longitude
                }
                batch.add_object(collection=CLASS_NAME, properties=obj)  # ✅ Updated method
                print(f"✅ Added: {outlet.name}")

        print(f"✅ Successfully uploaded {len(outlets)} Subway outlets to Weaviate.")

# ✅ Run the ingestion script
if __name__ == "__main__":
    ingest_data()
    client.close()  # ✅ Close connection to avoid memory leaks
