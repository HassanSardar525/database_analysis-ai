from app.agent.nodes import get_schema_node, generate_sql_node, execute_sql_node

# Simulate a starting state
state = {"query": "How many customers are in the Enterprise plan?", "retry_count": 0}

# Step 1: Get Schema
state.update(get_schema_node(state))
print("✅ Schema Retrieved")

# Step 2: Generate SQL
state.update(generate_sql_node(state))
print(f"✅ Generated SQL: {state['sql_query']}")

# Step 3: Execute
state.update(execute_sql_node(state))
print(f"✅ Results: {state['results']}")