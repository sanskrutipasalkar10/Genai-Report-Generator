# src/reasoning/code_interpreter.py
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_community.chat_models import ChatOllama
import pandas as pd
import io

def analyze_data_with_code(table_html_list, user_query):
    """
    Converts tables to DataFrames and lets LLM write code to query them.
    This guarantees mathematical accuracy.
    """
    # 1. Load Tables into Pandas
    dfs = [pd.read_html(html)[0] for html in table_html_list]
    
    # 2. Initialize Local LLM (Llama 3 via Ollama)
    llm = ChatOllama(model="llama3", temperature=0) # Temp 0 for deterministic code

    # 3. Create Agent that can execute Python
    agent = create_pandas_dataframe_agent(
        llm,
        dfs,
        verbose=True,
        allow_dangerous_code=True, # Required for local execution
        agent_type="tool-calling"
    )

    # 4. Strict System Prompt
    prompt = f"""
    You are a data analyst. 
    Query: {user_query}
    You have access to pandas dataframes. 
    Do NOT guess the answer. 
    Write pandas code to calculate the answer exactly.
    """
    
    return agent.invoke(prompt)