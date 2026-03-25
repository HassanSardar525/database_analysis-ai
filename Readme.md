# 🏎️ DriveData AI: Autonomous Car Dealership Analyst

An intelligent, self-correcting data agent that transforms natural language into actionable business insights. Built with **LangGraph**, **Gemini 3 Flash**, and **Next.js**, this system doesn't just "chat"—it reasons, queries, and visualizes complex car dealership data in real-time.

---

## 🌟 Key Features

* **Autonomous Intent Routing:** Uses a "Gatekeeper" node to distinguish between data queries, structural metadata requests, and irrelevant chatter.
* **Self-Correction Loop:** Integrated LangGraph logic that detects SQL syntax errors, feeds them back to the LLM, and automatically retries with corrected queries.
* **Real-Time Streaming (SSE):** A low-latency user experience that streams the agent's "thought process" (e.g., *Analyzing Intent...* -> *Writing SQL...*) as it moves through the graph.
* **Semantic Metadata Layer:** Bridges the gap between raw PostgreSQL schemas and business logic for high-accuracy Text-to-SQL generation.
* **Production Observability:** Full tracing and debugging integrated via **LangSmith**.

---

## 🛠️ Tech Stack

**Frontend:** Next.js (App Router), Tailwind CSS, Recharts, Lucide Icons.  
**Backend:** FastAPI, LangGraph, LangChain, Python 3.12.  
**Intelligence:** Gemini 3 Flash (LLM).  
**Database:** Neon (Serverless PostgreSQL).  

---

## 🧠 System Architecture

The agent follows a stateful directed acyclic graph (DAG):
1. **Schema Retrieval:** Fetches live database context.
2. **Intent Routing:** Decides if the query is a Data Task or should be Refused.
3. **SQL Generation:** Translates natural language to SQL using semantic metadata.
4. **Execution & Self-Correction:** Runs the query on Neon; if it fails, it loops back to step 3 with error logs.
5. **Insights & Visualization:** Summarizes data and generates chart configurations.

---

## 🚀 Challenges & Solutions (The "Engineering" Bit)

### Challenge: SQL Hallucinations & Syntax Errors
**Solution:** Implemented a recursive **Self-Correction Loop**. Instead of failing on a bad join, the agent captures the `psycopg2` error message, appends it to the prompt history, and re-invokes the LLM to patch the code. This reduced query failure rates by ~40%.

### Challenge: Latency & "Ghosting" in UI
**Solution:** Leveraged **Server-Sent Events (SSE)** to stream node updates. This allows the frontend to show granular status indicators, keeping the user engaged during multi-step reasoning processes.

---

## 🏁 Getting Started

### Backend Setup
1. `cd backend`
2. `poetry install`
3. Create a `.env` with `GOOGLE_API_KEY`, `DATABASE_URL`, and `LANGCHAIN_API_KEY`.
4. `poetry run python main.py`

### Frontend Setup
1. `cd frontend`
2. `npm install`
3. `npm run dev`