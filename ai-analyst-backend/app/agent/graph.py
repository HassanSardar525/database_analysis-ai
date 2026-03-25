from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agent.state import AgentState
from app.agent.nodes import (
    get_schema_node, 
    generate_sql_node, 
    execute_sql_node, 
    analyze_data_node, 
    format_chart_node,
    router_node,
    refusal_node
)

# Logic to decide if we should retry or continue
def should_continue(state: AgentState):
    if state.get("error") and state.get("retry_count", 0) < 3:
        print(f"🔄 Error detected, retrying... (Attempt {state['retry_count']})")
        return "generate_sql"
    return "analyze_data"

def route_intent(state: AgentState):
    """Conditional logic to pick the next node."""
    intent = state.get("intent")
    if intent == "data_task":
        return "get_schema"
    return "refuse_task" 

# Build the Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("router", router_node)
workflow.add_node("refuse_task", refusal_node)
workflow.add_node("get_schema", get_schema_node)
workflow.add_node("generate_sql", generate_sql_node)
workflow.add_node("execute_sql", execute_sql_node)
workflow.add_node("analyze_data", analyze_data_node)
workflow.add_node("format_chart", format_chart_node)

# 2. Define the Flow
workflow.set_entry_point("get_schema") # <--- START HERE
workflow.add_edge("get_schema", "router") # <--- THEN ROUTE

# 3. Conditional Logic after Routing
def route_decision(state: AgentState):
    if state["intent"] == "data_task":
        return "generate_sql"
    return "refuse_task"

workflow.add_conditional_edges(
    "router",
    route_decision,
    {
        "generate_sql": "generate_sql",
        "refuse_task": "refuse_task"
    }
)

# 4. The rest of the pipeline
workflow.add_edge("generate_sql", "execute_sql")
workflow.add_conditional_edges("execute_sql", should_continue)
workflow.add_edge("analyze_data", "format_chart")
workflow.add_edge("format_chart", END)
workflow.add_edge("refuse_task", END)


memory = MemorySaver()
# Compile the Graph WITH the checkpointer
app_graph = workflow.compile(checkpointer=memory) # <--- Pass it here