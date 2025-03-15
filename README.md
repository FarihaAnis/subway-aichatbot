# SUBWAY AICHATBOTS

## Overview
This document provides an overview of the Subway AI Chatbot's architecture, data pipeline, and troubleshooting, focusing on hybrid search, structured query handling, and LLM integration to ensure accurate and reliable responses. For backend, database, and frontend setup, refer to the README.md in their respective directories.

---

## Chatbot Architecture & Query Processing
This chatbot is designed using a hybrid approach that combines structured data retrieval and LLM-powered responses. Unlike traditional RAG (Retrieval-Augmented Generation), which retrieves unstructured text from a vector database and passes it to an LLM, this chatbot directly processes structured queries without relying on an LLM for factual accuracy.

### Key Components
◽Hybrid Retrieval (Vector + Keyword Search)
   - Uses Weaviate’s hybrid search to retrieve relevant Subway outlets based on semantic similarity (vector search) and exact keyword matches (filtering).
   - This allows it to retrieve structured outlet details (e.g., addresses, operating hours) with high accuracy.

◽Structured Query Handling (Without RAG)
   - Instead of passing all retrieved data to LLaMA 3, the chatbot processes structured queries separately:
      - Counting outlets: Uses handle_count_query() to return an exact count.
      - Sorting by closing time: Uses extract_closing_time() and convert_to_24_hour() to normalize and compare operating hours.
   - These queries are resolved without using the LLM, preventing hallucinations.

◽ LLM for Open-Ended Queries Only
   - LLaMA 3 is only used when natural language understanding is required (e.g., “Tell me about Subway in Bangsar”).
   - The chatbot formats retrieved outlet details and constructs a structured prompt before sending it to LLaMA 3.

◽ Preventing Hallucination
   - The chatbot only sends relevant, pre-processed data to LLaMA 3, instead of raw retrieval results.
   - This ensures accurate structured responses while still allowing flexibility for general queries.

<p align="center"><b>Query Processing Workflow For Retrieving and Responding To User Queries</b></p>
<p align="center">
  <img src="chatbot-workflow.png" alt="Chatbot Workflow">
</p>

---

Below diagram represents the data pipeline for the Subway AI Chatbot, showing the flow from data extraction and storage to processing and user interaction.

<p align="center"><b>End-to-End Data Flow for Chatbot</b></p>

<p align="center">
  <img src="chatbot-pipeline.png" alt="Chatbot Pipeline">
</p>

---

## ISSUE & TROUBLESHOOTING
### Webscrapping
🛑 **Issue**
- Only the first `<p>` inside `<div class="infoboxcontent">` was extracted, so the rest of the operating hours were missing because they were inside a nested `<div>` container, not directly under `<div class="location_left">`.

🛠️ **Troubleshooting & Fix**
- Extracted the full content inside `<div class="infoboxcontent">` using Selenium.
- Used `BeautifulSoup` to parse the extracted HTML and find all `<p>` elements inside it.
- Removed empty and irrelevant `<p>` elements, like "Find out more," using `BeautifulSoup` filtering.
- Separated address and operating hours (first `<p>` is the address).
- Merged multi-line operating hours if they were split across different `<p>` elements.
- Formatted the extracted data into a clean, structured response using `BeautifulSoup` processing.

---

### VectorDatabase
🛑 **Issue**
- Pinecone was used as the vector database to help the chatbot handle semantic queries. However, Pinecone is optimized for unstructured text search using embeddings and does not natively support filtering structured data like outlet names, addresses, and operating hours. This led to challenges in retrieving precise results, sometimes causing hallucinations in responses.

🛠️ **Troubleshooting & Fix**
- To address this, Weaviate was chosen instead because it supports both vector search (semantic similarity) and keyword-based filtering. This provides more flexibility in handling both structured data (e.g., filtering by city, exact outlet name) and unstructured queries.

---

### Inaccurate Responses Due to LLM Model Limitations in Handling Structured Data
🛑 **Issue**
- When users asked “How many outlets are located in Bangsar?”, the chatbot sometimes returned incorrect numbers because:
   - LLaMA 3 is a language model, not a database—it cannot perform exact counting.
   - Weaviate retrieves a limited subset of records, causing LLaMA 3 to estimate the count instead of providing an exact answer.
   - LLMs can hallucinate when handling numeric queries, leading to inconsistent responses.

🛠️ **Troubleshooting & Fix**
- To ensure accuracy, the chatbot now manually processes structured queries instead of relying on LLaMA 3.
- Implemented handle_count_query to directly count the number of outlets based on location.
- Retrieves relevant outlets from Weaviate before processing the count.
- Filters and matches location names accurately, preventing miscounts.
- Returns the exact count without using LLaMA 3, ensuring a reliable response.

🛑 **Issue**
- When users ask “Which Subway outlet closes the latest?”, the chatbot sometimes returns incorrect results because:
   - LLaMA 3 cannot sort operating hours correctly since they are stored as text in various formats.
   - Some outlets have multiple closing times, such as different hours for weekdays, weekends, and public holidays, making it harder to determine the latest closing time.
   - LLaMA 3 hallucinates responses, returning inconsistent results that do not answer the query accurately.

🛠️ **Troubleshooting & Fix**
- To resolve this issue, two functions, convert_to_24_hour(time_str) and extract_closing_time(hours_text), were added to properly process closing times before sorting. These functions ensure the chatbot:
   - Detects if the query is about closing times and determines the user's intent.
   - Retrieves relevant outlets from Weaviate using hybrid search.
   - Standardizes time formats to a 24-hour format for accurate comparison.
   - Extracts and processes operating hours, handling multiple closing times and public holiday variations.
   - Identifies the latest closing outlet and returns an accurate response, without relying on LLaMA 3.








