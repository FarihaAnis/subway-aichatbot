import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, Circle, Tooltip, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./App.css"; // ✅ Import CSS

// Default map center (Kuala Lumpur)
const CENTER = [3.140853, 101.693207];
const RADIUS = 5000; // 5KM in meters

// ✅ Custom Subway Icon
const subwayIcon = new L.Icon({
  iconUrl: "/subway-marker.png",
  iconSize: [25, 35],
  iconAnchor: [12, 35],
  popupAnchor: [0, -35]
});

// ✅ Function to Auto-Adjust Map to Fit All Markers
const FitBounds = ({ outlets }) => {
  const map = useMap();
  useEffect(() => {
    if (outlets.length > 0) {
      const bounds = L.latLngBounds(outlets.map(outlet => [outlet.latitude, outlet.longitude]));
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [outlets, map]);
  return null;
};

const App = () => {
  const [outlets, setOutlets] = useState([]);
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]); // ✅ Store full chat history
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ✅ Fetch Subway Outlets from FastAPI
  useEffect(() => {
    fetch("http://127.0.0.1:8000/outlets")
      .then(response => response.json())
      .then(data => setOutlets(data))
      .catch(error => {
        console.error("Error fetching outlets:", error);
        setError("Failed to load Subway outlets.");
      });
  }, []);

  // ✅ Function to Check 5KM Intersection
  const isIntersecting = (lat1, lon1, lat2, lon2) => {
    if (!lat1 || !lon1 || !lat2 || !lon2) return false; // ✅ Prevent crashes if missing data

    const toRad = (angle) => (Math.PI * angle) / 180;
    const R = 6371000; // Earth radius in meters
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;
    return distance <= RADIUS;
  };

  // ✅ Handle Chatbot Query
  const handleChatbotQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);

    const newMessages = [...messages, { sender: "user", text: query }]; // ✅ Append user message
    setMessages(newMessages);
    setQuery("");

    try {
      const response = await fetch("http://127.0.0.1:8000/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ query })
      });

      const data = await response.json();
      setMessages([...newMessages, { sender: "bot", text: data.response }]); // ✅ Append bot response
    } catch (error) {
      console.error("Error fetching chatbot response:", error);
      setError(error.message);
    }

    setLoading(false);
  };

  return (
    <div className="App">
      <h1 className="main-title">
      <img src="/subway-logo.png" alt="Subway Logo" className="main-logo" />
        ubway Outlets in Kuala Lumpur
      </h1>

      <div className="container">
        {/* ✅ Map Section (Left Side) */}
        <div className="map-wrapper">
          <MapContainer center={CENTER} zoom={12} className="map-container">
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OpenStreetMap contributors" />
            <FitBounds outlets={outlets} />

            {outlets.map((outlet, index) => {
              let isHighlighted = outlets.some((otherOutlet, i) =>
                i !== index && isIntersecting(
                  outlet.latitude, outlet.longitude,
                  otherOutlet.latitude, otherOutlet.longitude
                )
              );

              return (
                <Marker key={index} position={[outlet.latitude, outlet.longitude]} icon={subwayIcon}>
                  <Tooltip direction="top" offset={[0, -25]} opacity={1} permanent={false}>
                    <strong>{outlet.name}</strong>
                  </Tooltip>
                  <Popup>
                    <strong>{outlet.name}</strong><br />
                    {outlet.address}<br />
                    ⏰ {outlet.operating_hours} <br />
                    <a href={outlet.waze_link} target="_blank" rel="noopener noreferrer">🚗 Open in Waze</a>
                  </Popup>
                  {/* ✅ Highlight Intersecting Outlets */}
                  <Circle 
                    center={[outlet.latitude, outlet.longitude]} 
                    radius={RADIUS} 
                    fillOpacity={0.03} 
                    color={isHighlighted ? "#FFC20D" : "#007bff"} 
                    weight={isHighlighted ? 1 : 2}
                  />
                </Marker>
              );
            })}
          </MapContainer>
        </div>

        {/* ✅ Chatbot UI (Right Side) */}
        <div className="chatbot-container">
          <h2 className="chatbot-title">Welcome to Subway Chat!
          <img src="/sandwich-logo.png" alt="Subway Logo" className="chatbot-logo" />
          </h2>
          <div className="chatbot-messages">
            {messages.map((msg, index) => (
              <div key={index} className={`chat-bubble ${msg.sender === "user" ? "user-bubble" : "bot-bubble"}`}>
                {/* ✅ Use `dangerouslySetInnerHTML` only for bot messages */}
                {msg.sender === "bot" ? (
                  <div dangerouslySetInnerHTML={{ __html: msg.text }} />
                ) : (
                  msg.text
                )}
              </div>
            ))}
            {loading && <div className="loading-bubble">Typing...</div>} {/* ✅ Typing Animation */}
          </div>

          {/* ✅ Input Section */}
          <div className="chatbot-input-container">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask about Subway outlets..."
              className="chatbot-input"
            />
            <button onClick={handleChatbotQuery} disabled={loading} className="chatbot-button">
              {loading ? "Searching..." : "Send"}
            </button>
          </div>

          {error && <p className="chatbot-error">{error}</p>}
        </div>
      </div>
    </div>
  );
};

export default App;
