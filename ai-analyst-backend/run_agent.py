from app.agent.graph import app_graph
from langchain_core.messages import HumanMessage

def run_test():
    config = {"configurable": {"thread_id": "session_1"}}
    
    # --- TURN 1 ---
    print("🚀 TURN 1: How many customers?")
    inputs = {
        "messages": [HumanMessage(content="How many customers do we have?")],
        "results": [],  # Initialize to avoid KeyErrors
        "retry_count": 0
    }
    
    for output in app_graph.stream(inputs, config):
        pass
    
    state = app_graph.get_state(config).values
    print(f"🤖 AI: {state.get('explanation')}")

    # --- TURN 2 (Follow-up) ---
    print("\n🔄 TURN 2: Follow-up")
    # Notice we ONLY send the new message; MemorySaver handles the rest!
    inputs2 = {"messages": [HumanMessage(content="And how many are from the USA?")]}
    
    for output in app_graph.stream(inputs2, config):
        pass
        
    state = app_graph.get_state(config).values
    print(f"🤖 AI: {state.get('explanation')}")

if __name__ == "__main__":
    run_test()