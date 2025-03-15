from pydantic import BaseModel
from typing import Optional

# ✅ Define API Response Schema
class SubwayOutletSchema(BaseModel):
    id: int
    name: str
    address: str
    operating_hours: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    waze_link: Optional[str] = None

    class Config:
         from_attributes = True  # ✅ Replace 'orm_mode' with 'from_attributes'

# ✅ Define Request Schema for Chatbot Query
class ChatbotRequest(BaseModel):
    query: str  # ✅ Expects JSON { "query": "your question" }