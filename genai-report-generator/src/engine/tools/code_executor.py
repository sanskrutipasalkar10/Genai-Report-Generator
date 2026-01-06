import pandas as pd
import sys
import re
from io import StringIO
import contextlib

class DataTools:
    """
    A Generalizable Toolbox for the LLM. 
    Handles complex Pandas syntax and Sheet Selection logic.
    """
    def get_active_sheet(self, dfs):
        """
        Smartly selects the most relevant sheet from the dictionary.
        Prioritizes sheets with 'FY', 'Year', or 'Summary' in the name.
        Fallback: Returns the first sheet found.
        """
        if not dfs or not isinstance(dfs, dict):
            return pd.DataFrame()
        
        # 1. Heuristic: Look for Summary/Yearly sheets
        for key in dfs.keys():
            key_str = str(key).lower()
            if "fy" in key_str or "year" in key_str or "summary" in key_str:
                return dfs[key]
        
        # 2. Fallback: Return the first sheet
        try:
            return list(dfs.values())[0]
        except IndexError:
            return pd.DataFrame()

    def get_value(self, df, row_label, col_label):
        """
        Finds a value in a Row-Based dataframe (e.g., Financial P&L).
        Usage: tools.get_value(df, 'Revenue', 'Consolidated')
        """
        try:
            # 1. Identify the search column (usually the first one, renamed to Line_Item)
            if df.empty: return 0.0
            search_col = df.columns[0]
            
            # 2. Case-insensitive, partial match search
            mask = df[search_col].astype(str).str.contains(row_label, case=False, na=False)
            row = df[mask]
            
            if not row.empty:
                # 3. Extract and clean the value
                val = row[col_label].values[0]
                return pd.to_numeric(val, errors='coerce')
            return 0.0
        except Exception:
            return 0.0

    def get_column_sum(self, df, col_label):
        """
        Sums a column in a Column-Based dataframe (e.g., Sales Data).
        Usage: tools.get_column_sum(df, 'Sales')
        """
        try:
            if col_label in df.columns:
                return pd.to_numeric(df[col_label], errors='coerce').sum()
            return 0.0
        except Exception:
            return 0.0

def execute_python_code(code: str, data: dict) -> str:
    output_buffer = StringIO()
    
    code_match = re.search(r"```(?:\w+)?\n(.*?)```", code, re.DOTALL)
    clean_code = code_match.group(1).strip() if code_match else code.replace("```", "").strip()

    # 🟢 INJECT THE UPDATED TOOLBOX
    tools = DataTools()

    local_scope = {
        "dfs": data, 
        "pd": pd,
        "tools": tools, # The LLM can now use 'tools.get_active_sheet()'
        "df": data      # Fallback
    }
    
    try:
        with contextlib.redirect_stdout(output_buffer):
            exec(clean_code, {}, local_scope)
        
        result = output_buffer.getvalue()
        if not result:
            return "Code executed successfully."
        return result.strip()
        
    except Exception as e:
        return f"Error executing code: {str(e)}"