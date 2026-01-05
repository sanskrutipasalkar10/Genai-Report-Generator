import pandas as pd
from langchain_core.messages import SystemMessage
from src.engine.llm import get_llm

SCANNER_PROMPT = """
You are a Data Strategist.
I will give you the Schema (Columns & Types) of a dataset found in a file.

YOUR TASK:
1. Analyze what the data represents (Sales, Inventory, HR, etc.).
2. List 3-5 specific, valuable calculations we can do with this data.
3. Output a clean summary to the user.

EXAMPLE INPUT:
Columns: [Date, Product_ID, Units_Sold, Unit_Price]

EXAMPLE OUTPUT:
"I have detected a Sales Dataset. 
We can calculate:
1. Total Revenue (Units * Price)
2. Top selling products
3. Monthly sales trends."
"""

def scanner_agent(dfs: list[pd.DataFrame]):
    """
    Analyzes the extracted DataFrames and reports capabilities to the user.
    """
    if not dfs:
        return "No tabular data found in this document. I will proceed with text summarization only."

    # For simplicity, we analyze the first major table found
    # In production, we might merge similar tables
    main_df = dfs[0] 
    
    schema_info = main_df.dtypes.to_string()
    sample_data = main_df.head(3).to_markdown()

    context = f"""
    DATA SCHEMA FOUND:
    {schema_info}
    
    SAMPLE DATA:
    {sample_data}
    """
    
    # Call LLM
    llm = get_llm(model_type="reasoning")
    messages = [
        SystemMessage(content=SCANNER_PROMPT),
        SystemMessage(content=context)
    ]
    
    response = llm.invoke(messages)
    
    return {
        "analysis_summary": response.content,
        "primary_dataframe": main_df # We pass this forward to the Analyst
    }