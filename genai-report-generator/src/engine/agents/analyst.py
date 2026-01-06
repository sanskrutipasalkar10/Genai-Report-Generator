import yaml
from pathlib import Path
from langchain_core.messages import SystemMessage
from src.engine.llm import get_llm
from src.engine.tools.code_executor import execute_python_code
import pandas as pd

# Define the directory where prompts are stored
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def analyst_agent(state):
    """
    Analyst Agent (Professional Edition).
    
    Capabilities:
    1. Multi-Sheet Analysis: Handles a dictionary of DataFrames.
    2. Dynamic Strategy: Switches between 'Row-Based' (Financial) and 'Column-Based' (Operational) logic.
    3. Schema Injection: Provides context for all available sheets.
    """
    
    # 1. Unpack State
    messages = state.get('messages', [])
    dfs = state.get('data') # Expecting Dict[str, pd.DataFrame]
    
    # Get configuration from the Inspector Agent (defaults to Operational if missing)
    config = state.get('config', {}) 
    report_type = config.get('report_type', 'OPERATIONAL')
    data_structure = config.get('data_structure', 'COLUMN_BASED')

    print(f"--- 🤖 Analyst Agent: Activated {report_type} Mode ({data_structure}) ---")

    # --- SAFETY CHECK: NO DATA ---
    if not dfs or not isinstance(dfs, dict):
        return {
            "messages": messages,
            "final_answer": "No structured data tables found. Skipping analysis."
        }

    # 2. Select the Correct Prompt Strategy
    # We choose the prompt based on the data structure detected by the Inspector
    if data_structure == "ROW_BASED" or report_type == "FINANCIAL":
        prompt_file = "analyst_financial.yaml"
    else:
        prompt_file = "analyst_operational.yaml"
    
    prompt_path = PROMPTS_DIR / prompt_file
    
    # Safety check for prompt existence
    if not prompt_path.exists():
        # Fallback to operational if specific prompt is missing
        print(f"⚠️ Warning: {prompt_file} not found. Falling back to operational.")
        prompt_path = PROMPTS_DIR / "analyst_operational.yaml"

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_config = yaml.safe_load(f)

    # 3. Build Multi-Sheet Schema Context
    # We need to show the LLM what sheets exist and what columns they have
    schema_context = "AVAILABLE DATA TABLES (dfs dictionary):\n"
    
    for sheet_name, df in dfs.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            schema_context += f"\n--- Sheet/Table Name: '{sheet_name}' ---\n"
            schema_context += f"Columns: {list(df.columns)}\n"
            
            # Show the first 3 rows so the LLM sees the data format
            # (Crucial for seeing if 'Line_Item' contains 'Revenue')
            try:
                sample = df.head(3).to_markdown(index=False)
            except ImportError:
                sample = df.head(3).to_string(index=False)
                
            schema_context += f"Sample Data:\n{sample}\n"

    # 4. Initialize LLM
    llm = get_llm(model_type="reasoning")
    
    # 5. Inject Schema into System Prompt
    full_instruction = prompt_config.get('instruction', '') + "\n\n" + schema_context
    sys_msg = SystemMessage(content=full_instruction)
    
    # 6. Generate Code
    # The LLM now sees the User Query + The System Instructions + The Data Schema
    response = llm.invoke([sys_msg] + messages)
    generated_code = response.content
    print(f"--- 📝 Generated Code ---\n{generated_code}")
    
    # 7. Execute Code
    # We pass the WHOLE dictionary of dataframes ('dfs') to the executor
    execution_result = execute_python_code(generated_code, dfs)
    print(f"--- 📊 Execution Result ---\n{execution_result}")
    
    return {
        "messages": [response],
        "final_answer": execution_result
    }