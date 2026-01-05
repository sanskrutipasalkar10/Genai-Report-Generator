import yaml
from pathlib import Path
from langchain_core.messages import SystemMessage
from src.engine.llm import get_llm
from src.engine.tools.code_executor import execute_python_code
import pandas as pd

# Load prompt configuration
# Ensure the path resolves correctly relative to this file
PROMPT_PATH = Path(__file__).parent.parent / "prompts/analyst.yaml"

# Safety check for the prompt file
if not PROMPT_PATH.exists():
    raise FileNotFoundError(f"Prompt file not found at {PROMPT_PATH}")

with open(PROMPT_PATH, "r") as f:
    prompt_config = yaml.safe_load(f)

def analyst_agent(state):
    """
    Analyst Agent with Schema Awareness.
    Takes a state dict containing 'messages' and 'data' (DataFrame).
    """
    print("--- 🤖 Analyst Agent: Analyzing Request ---")
    
    messages = state.get('messages', [])
    data = state.get('data') # This could be a DataFrame or None
    
    # --- LOGIC BRANCH 1: TEXT FILES (Safety Check) ---
    if data is None or not isinstance(data, pd.DataFrame):
        return {
            "messages": messages,
            "final_answer": "The input file is text-based or empty. No calculation performed."
        }

    # --- LOGIC BRANCH 2: NUMERICAL DATA ---
    df = data
    
    # 1. Extract Schema & Sample Data
    schema_info = df.dtypes.to_string()
    # Handle empty dataframes gracefully
    if not df.empty:
        sample_data = df.head(3).to_markdown(index=False)
    else:
        sample_data = "No data available"
    
    data_context = f"""
    DATA SCHEMA:
    {schema_info}

    SAMPLE DATA (First 3 rows):
    {sample_data}
    """

    print(f"--- 📋 Detected Schema ---\n{schema_info}")

    # 2. Initialize LLM
    llm = get_llm(model_type="reasoning")
    
    # 3. Inject Schema into System Prompt
    full_instruction = prompt_config.get('instruction', '') + "\n\n" + data_context
    
    sys_msg = SystemMessage(content=full_instruction)
    
    # 4. Generate Code
    # We pass the system message + user messages
    response = llm.invoke([sys_msg] + messages)
    generated_code = response.content
    print(f"--- 📝 Generated Code ---\n{generated_code}")
    
    # 5. Execute Code
    execution_result = execute_python_code(generated_code, df)
    print(f"--- 📊 Execution Result ---\n{execution_result}")
    
    return {
        "messages": [response],
        "final_answer": execution_result
    }