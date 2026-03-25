from typing import Annotated, List, TypedDict
from operator import add
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    schema: str
    sql_query: str
    results: List[dict]
    error: str
    explanation: str
    chart_data: dict
    retry_count: int
    intent: str  # <--- Ensure this is added!