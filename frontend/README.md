## Frontend Setup Guide
1. **Create a `frontend` folder**
2. **Initialize a React App inside the folder:**
   ```sh
   npx create-react-app .
   ```
   - Open a command prompt (cmd) and navigate to the frontend folder. 
   - After running `npx create-react-app .`, the project structure, necessary configuration files (`package.json`, `.gitignore`), folders (`src/, public/, node_modules/`), and default React components are created.
3. **Place necessary images inside the `public` folder**
   - subway-logo.png
   - sandwich-logo.png
   - subway-marker.png

### Implementation of Frontend Code
1. **Open `App.js`**
2. **Import required modules**
   - React Hooks (useState, useEffect) for state management.
   - React-Leaflet components for map visualization (MapContainer, TileLayer, Marker, Popup, Circle, Tooltip, useMap).
   - Leaflet for custom Subway outlet markers.
   - CSS file (`App.css`) for styling the UI.

#### Map Visualization Setup Guide
3. **Define constants**
     - CENTER: Default map center (Kuala Lumpur coordinates).
     - RADIUS: Defines the 5KM radius for nearby Subway outlets.
     - Custom Subway Icon using L.Icon:
       - Loads an image for the map marker (`subway-marker.png from public/`).
       - Adjusts icon size and positioning to ensure proper display on the map.
4. **Auto-Fit Map to Display All Outlets**
     - FitBounds Component automatically adjusts the map to fit all Subway outlet markers.
     - Uses LatLngBounds (a class in Leaflet) to set the view based on the locations of all outlets.
5. **Fetch Subway Outlet Data from FastAPI**
     - Retrieves Subway outlet data from the FastAPI backend (`http://127.0.0.1:8000/outlets`).
     - Displays outlets using Marker components.
     - Highlights outlets within 5KM using the Haversine formula:
      -  Calculates the distance between outlets.
      -  Yellow circle for outlets within 5KM of another outlet, otherwise blue circle 

#### Chatbot UI Setup Guide
6. **Manage Chatbot State**
   - messages: Stores chat history (user queries + bot responses).
   - query: Stores user input before submission.
   - loading: Shows loading state when waiting for a bot response.
   - error: Handles API request failures (e.g., if the chatbot is unreachable).
7. **Handle Chatbot Queries (handleChatbotQuery)**
   - Appends user input to messages.
   - Sends the query to FastAPI chatbot API (`http://127.0.0.1:8000/chatbot`).
   - Updates messages with the bot's response after API returns data.
8. **Chatbot UI**
   - Messages are generated and updated dynamically based on:
     - User Input – When the user types and submits a message.
     - Bot Response – When the chatbot processes the query and replies.
     - Chat History – Messages are continuously stored and displayed. 
   - Formatted Chatbot Responses
     - dangerouslySetInnerHTML is used only for bot responses to support:
         - Hyperlinks (e.g., “Navigate Here” for Waze).
         - Bold text, bullet points, and other HTML formatting.
   - Include typing indicator
     - Shows a "Typing..." message while waiting for a response.
   - Input Field & Send Button:
     - Allows users to enter a query and send it to the chatbot.
     - The button is disabled when waiting for a response (prevents multiple requests).
9. **Update UI Styling in App.css**
   - Adjust layout and styling for the map and chatbot UI.
   - Apply flexbox to structure the layout properly.
   - Style chatbot messages for better readability and user experience.
   - Use media queries for responsive design across different screen sizes.
10. **To launch the UI, run `npm start` in the cmd terminal.**