import uvicorn
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.messages import BaseMessage 
from app.schema.api_models import ChatRequest, ChatResponse
from app.agent.graph import app_graph
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="AI Data Analyst API")

# Allow your Next.js frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # 1. Prepare inputs for LangGraph
        config = {"configurable": {"thread_id": request.thread_id}}
        inputs = {
            "messages": [HumanMessage(content=request.message)],
            "retry_count": 0,
            "results": []
        }

        # 2. Run the Graph (Synchronously for now, Streaming is advanced)
        # We use app_graph.invoke() to get the final state once everything finishes
        final_state = app_graph.invoke(inputs, config)

        # 3. Return the structured response
        return ChatResponse(
            explanation=final_state.get("explanation", "No explanation generated."),
            sql=final_state.get("sql_query", "No SQL generated."),
            chart_data=final_state.get("chart_data"),
            thread_id=request.thread_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# main.py



@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        config = {"configurable": {"thread_id": request.thread_id}}
        inputs = {
            "messages": [HumanMessage(content=request.message)], 
            "retry_count": 0,
            "results": [] # Initializing as we did before
        }

        async for event in app_graph.astream(inputs, config, stream_mode="updates"):
            safe_event = {}
            # --- NEW: Serialization Helper ---
            # We need to make sure the event dictionary only contains JSON-safe types
            safe_event = {}
            for node_name, node_output in event.items():
                
                if node_output is None:
                    continue

                safe_output = {}
                if isinstance(node_output, dict):
                    for key, value in node_output.items():
                        # If the value is a list of messages, convert them to strings/dicts
                        if key == "messages" and isinstance(value, list):
                            safe_output[key] = [
                                {"role": m.type, "content": m.content} if isinstance(m, BaseMessage) else m 
                                for m in value
                            ]
                        else:
                            safe_output[key] = value    
                safe_event[node_name] = safe_output

            # Now json.dumps will work perfectly
            if safe_event:
                 yield {
                "event": "update",
                "data": json.dumps(safe_event)
            }
            
    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)