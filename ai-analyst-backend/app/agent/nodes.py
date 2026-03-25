import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agent.state import AgentState
from app.tools.db import db_manager
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages import AIMessage
import json
import re

# Initialize Gemini 1.5 Flash (Fast and efficient for SQL)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

def get_schema_node(state: AgentState):
    try:
        # 1. Get the actual technical schema from your DB manager
        raw_schema = db_manager.get_schema() 

        # 2. Define the Semantic Metadata (The "Secret Sauce")
        # This helps the AI understand the business logic
        metadata_hints = """
        === BUSINESS METADATA & HINTS ===
        - Table 'vehicles': Contains all cars currently or previously in stock.
            - 'body_type': Standard categories are 'SUV', 'Sedan', 'Truck', 'Coupe'. Use these for grouping.
            - 'status': Use 'Available' for current inventory and 'Sold' for past sales.
        - Table 'brands': Contains the names of car manufacturers (Toyota, BMW, etc.).
            - JOIN 'vehicles.brand_id' with 'brands.id' to filter by brand name.
        - Table 'sales': Contains transaction records.
            - 'sale_price' is the final price paid, 'sale_date' is when it happened.
        =================================
        """

        # 3. Combine them into one "Super Schema"
        full_context = f"{metadata_hints}\n\nTECHNICAL SCHEMA:\n{raw_schema}"
        
        return {"schema": full_context, "error": None}
    except Exception as e:
        # If the DB connection fails, we report it here
        return {"error": f"Database Connection Error: {str(e)}", "schema": ""}


def generate_sql_node(state: AgentState):
    # Format the history so Gemini understands the context better
    history = "\n".join([f"{m.type}: {m.content}" for m in state["messages"]])
    
    prompt = prompt = f"""
You are an expert PostgreSQL query generator.

Your goal is to convert a user question into a SAFE and CORRECT SQL SELECT query.

=====================
DATABASE SCHEMA:
{state['schema']}
=====================

USER QUESTION:
{state['messages'][-1].content}

CONTEXT (optional history):
{history}

=====================
RULES:

1. ONLY generate a SELECT query. Never use INSERT, UPDATE, DELETE, DROP, ALTER.
2. ONLY use tables and columns that EXIST in the schema.
3. If a column/table is not clearly present, DO NOT guess — instead return:
   SELECT 'ERROR: Unknown column or table' AS error;

4. Always:
   - Use explicit column names (avoid SELECT *)
   - Use proper JOINs if needed
   - Add LIMIT 100 unless aggregation is used

5. If the question is ambiguous:
   - Choose the MOST reasonable interpretation based on schema
   - Do NOT ask questions

6. If aggregation is needed:
   - Use GROUP BY correctly

=====================
OUTPUT FORMAT:

Return ONLY raw SQL.
No markdown.
No explanation.
No backticks.

=====================
"""
    response = llm.invoke(prompt)
    # Clean the SQL just in case Gemini ignored the "no markdown" rule
    sql = response.content.replace("```sql", "").replace("```", "").strip()
    return {"sql_query": sql, "retry_count": state.get("retry_count", 0) + 1}

def validate_sql(sql: str) -> bool:
    """Returns True if the SQL is a safe SELECT query."""
    # 1. Convert to uppercase for checking
    sql_upper = sql.upper()
    
    # 2. Blacklisted keywords (destructive operations)
    blacklist = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER", "GRANT"]
    if any(word in sql_upper for word in blacklist):
        return False
        
    # 3. Whitelist: Must start with SELECT
    if not sql_upper.strip().startswith("SELECT"):
        return False
        
    return True

def execute_sql_node(state: AgentState):
    sql = state["sql_query"]
    
    # Check Guardrail
    if not validate_sql(sql):
        return {"error": "Security Block: Only SELECT queries are allowed.", "results": []}

    # Automatically Inject LIMIT 100 if not present
    if "LIMIT" not in sql.upper():
        sql = f"{sql.rstrip(';')} LIMIT 100;"

    try:
        results = db_manager.execute_query(sql)
        return {"results": results, "error": None, "sql_query": sql}
    except Exception as e:
        return {"error": str(e), "results": []}

def analyze_data_node(state: AgentState):
    # 1. Error Handling: If we reached here with an error, explain it
    if state.get("error") and not state.get("results"):
        msg = f"I'm sorry, I couldn't retrieve that data. Technical error: {state['error']}"
        return {"explanation": msg, "messages": [AIMessage(content=msg)]}

    # 2. Define the Prompt
    prompt = f"""
You are a data analyst.

USER QUESTION:
{state['messages'][-1].content}

QUERY RESULTS:
{state['results']}

=====================
TASK:
1. Answer the user's question directly using the data.
2. Highlight key insights, trends, or anomalies.
3. If data is empty → explain clearly.
4. Keep it concise but informative.

=====================
STYLE:
- Natural language
- No raw JSON
- No repetition of raw rows
- Summarize instead of dumping data
=====================
"""

    # 3. THE FIX: Actually call the model!
    response = llm.invoke(prompt)

    # 4. Return the result
    return {
        "explanation": response.content, 
        "messages": [AIMessage(content=response.content)]
    }

def format_chart_node(state: AgentState):
    """Gemini decides if a chart is necessary and formats it."""
    results = state.get("results", [])
    
    # 1. Quick bypass for empty or non-numeric metadata results
    if not results or len(results) < 1:
        return {"chart_data": None}

    prompt = f"""
    You are a Data Visualizer. Analyze these results: {results}
    
    TASK:
    1. Determine if this data can be visualized (needs at least one numeric column and one category/date).
    2. If the user asked a general question (e.g., "What is this database about?") or the data is a single text value, return {{"type": "none"}}.
    3. Otherwise, return a JSON object:
       {{
         "type": "bar" | "pie" | "line",
         "labels": ["Label1", "Label2"],
         "values": [10, 20]
       }}
    
    ONLY return the raw JSON. No markdown.
    """
    response = llm.invoke(prompt)
    try:
        clean_json = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        # If AI said 'none', return None to the state
        if data.get("type") == "none":
            return {"chart_data": None}
        return {"chart_data": data}
    except:
        return {"chart_data": None}


def router_node(state: AgentState):
    """Decides if the question is relevant based on the ACTUAL database schema."""
    
    prompt = prompt = f"""
You are an intelligent query router for a database assistant.

=====================
DATABASE SCHEMA:
{state['schema']}
=====================

USER INPUT:
{state['messages'][-1].content}

=====================
TASK:
    Decide if this question belongs in the Data Pipeline.
    
1. 'data_task': 
   - Questions about metrics (revenue, sales, mileage).
   - Questions about database structure (schema, tables, columns, what data is available).
   - Requests for charts or lists of data.

2. chat_task:
   - Greetings, casual talk
   - General explanation requests

3. refuse_task:
   - Completely unrelated to database
   - Requires external knowledge not in schema

=====================
STRICT RULES:

- If ANY part of the question relates to schema → data_task
- If unsure → choose data_task (bias toward execution)
- Only choose refuse_task if clearly irrelevant

=====================
OUTPUT:

Return ONLY one word:
data_task OR chat_task OR refuse_task
"""
    response = llm.invoke(prompt).content.strip().lower()
    return {"intent": response}

def refusal_node(state: AgentState):
    """Handles irrelevant queries gracefully."""
    msg = "I'm specialized in your SaaS data. I can't help general topics, but I'm ready to analyze your database and give trends!"
    return {
        "explanation": msg, 
        "messages": [AIMessage(content=msg)],
        "chart_data": None
    }