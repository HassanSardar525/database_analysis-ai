from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default_user"

class ChatResponse(BaseModel):
    explanation: str
    sql: str
    chart_data: Optional[Dict[str, Any]]
    thread_id: str