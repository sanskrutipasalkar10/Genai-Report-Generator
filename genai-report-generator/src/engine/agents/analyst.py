import yaml
import pandas as pd
import numpy as np
import sys
import io
import re
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage
from src.engine.llm import get_llm

# Define the directory where prompts are stored
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def extract_code_block(text):
    """Extracts Python code from Markdown backticks."""
    match = re.search(r"```python(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()  # Fallback if no backticks

def analyst_agent(state):
    """
    Analyst Agent (Professional Edition).
    
    Capabilities:
    1. Multi-Sheet Analysis: Handles a dictionary of DataFrames.
    2. Dynamic Strategy: Switches between 'Row-Based' (Financial) and 'Column-Based' (Operational) logic.
    3. Schema Injection: Provides context for all available sheets.
    4. Self-Contained Execution: Runs code locally with correct variable mapping.
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
    # If dfs is None or empty, return immediately (Writer will handle text)
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
        print(f"⚠️ Warning: {prompt_file} not found. Falling back to operational.")
        prompt_path = PROMPTS_DIR / "analyst_operational.yaml"

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_config = yaml.safe_load(f)

    # 3. Build Multi-Sheet Schema Context
    # We need to show the LLM what sheets exist and what columns they have
    schema_context = "AVAILABLE DATA TABLES (variable name: `dfs`):\n"
    
    for sheet_name, df in dfs.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            schema_context += f"\n--- Sheet/Table Name: '{sheet_name}' ---\n"
            schema_context += f"Columns: {list(df.columns)}\n"
            
            # Show the first 3 rows so the LLM sees the data format
            try:
                sample = df.head(3).to_markdown(index=False)
            except ImportError:
                sample = df.head(3).to_string(index=False)
                
            schema_context += f"Sample Data:\n{sample}\n"

    # 4. Initialize LLM
    llm = get_llm(model_type="reasoning")
    
    # 5. Inject Schema into System Prompt
    base_instruction = prompt_config.get('instruction', '')
    full_instruction = f"{base_instruction}\n\n{schema_context}"
    
    # Explicitly remind LLM about the variable name
    user_task = f"{messages[-1].content}\n\nIMPORTANT: The data is loaded in a dictionary named `dfs`. Use `dfs['sheet_name']` or iterate `dfs.values()`."

    prompt_messages = [
        SystemMessage(content=full_instruction),
        HumanMessage(content=user_task)
    ]
    
    print("⚡ Sending REST Request to qwen3-coder:480b-cloud...")
    
    # 6. Generate Code
    response = llm.invoke(prompt_messages)
    generated_code = extract_code_block(response.content)
    
    print("--- 📝 Generated Code ---")
    print(generated_code)
    
    # 7. Execute Code (Self-Contained Sandbox)
    # Capture print() output
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    
    result_output = ""
    
    try:
        # 🟢 CRITICAL FIX: Map the input 'dfs' to the execution context
        # This ensures the AI's code (which uses 'dfs') can find the data.
        execution_context = {
            "dfs": dfs,       # <--- The Mapping Fix
            "pd": pd,
            "np": np
        }
        
        # Execute the code in this sandbox
        exec(generated_code, execution_context)
        
        result_output = new_stdout.getvalue()
        if not result_output.strip():
            result_output = "Code executed successfully but printed no output."
        
    except Exception as e:
        result_output = f"Error executing code: {e}"
    
    finally:
        sys.stdout = old_stdout # Restore terminal output

    print("--- 📊 Execution Result ---")
    print(result_output)
    
    return {
        "messages": [response],
        "final_answer": result_output
    }