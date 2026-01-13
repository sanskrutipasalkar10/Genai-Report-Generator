import pandas as pd
import sys
import os

# Add project root to path to ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.engine.llm import get_llm
from src.engine.tools.code_executor import execute_python_code

class AnalystAgent:
    def __init__(self):
        self.llm = get_llm()
        self.debug_mode = os.getenv("DEBUG_MODE", "True").lower() == "true"

    def perform_analysis(self, df: pd.DataFrame, plan: dict):
        """
        Executes the analysis plan by generating and running Python code.
        Args:
            df (pd.DataFrame): The clean data.
            plan (dict): The strategy from the Inspector Agent.
        """
        print(f"\n👨‍💻 [Analyst] Generating Code Strategy...")

        # 1. Construct the Prompt
        # We give the LLM the columns and the explicit plan to follow.
        columns = list(df.columns)
        
        prompt = f"""
        You are a Senior Python Data Analyst.
        
        ### DATA CONTEXT
        - **Variable Name:** `df`
        - **Columns:** {columns}
        - **Sample Data (First 2 rows):**
        {df.head(2).to_dict(orient='records')}

        ### ANALYSIS PLAN (From Inspector)
        {plan}

        ### YOUR TASK
        Write a Python script to execute this analysis.
        1. **Group By** the dimensions listed in the plan.
        2. **Aggregate** (Sum/Mean) the metrics listed.
        3. **PRINT** the results clearly using `print()`.
        
        ### CRITICAL RULES
        - **DO NOT** load the data. `df` is already defined in the environment.
        - **DO NOT** use `plt.show()`. Only print text/tables.
        - Wrap your code in ```python``` blocks.
        ### ⚠️ CRITICAL LOGIC RULES (DO NOT IGNORE):
            1. **DO NOT SUM COLUMNS BLINDLY:** Financial data often mixes Revenue (positive) and Expenses (negative) in the same column. 
               - If asked for **Revenue**, filter rows: `df[df['Metric'].str.contains('Revenue', case=False)]`.
               - If asked for **Expenses**, filter rows: `df[df['Metric'].str.contains('Expense|Cost', case=False)]`.
               - **NEVER** run `df['Column'].sum()` on a P&L statement unless calculating Net Profit.

            2. **HANDLING NEGATIVES:** - Expenses might be negative. When comparing "Magnitude" or plotting, use `.abs()`.
            
            3. **IGNORE TOTAL ROWS:** - If the data contains rows like "Total", "Consolidated", or "EBITDA", do not sum them with the individual line items, or you will double-count.
        


        ### FINANCIAL LOGIC RULES:
            1. **REVENUE vs EXPENSE:** Never sum a whole column if it contains both Revenue (Positive) and Expenses (Negative). You will get Net Profit, not Total Revenue.
            2. **FILTERING:** To get "Total Revenue", you must filter the dataframe:
               `revenue = df[df['Metric'].str.contains('Revenue', case=False)]['JLR'].sum()`
            3. **ABSOLUTE VALUES:** When plotting "Top Costs", convert negative expense numbers to positive values using `.abs()` so they show up on charts.
            
        """
        

        # 2. DEBUG: Print "Thinking" (Input Prompt)
        if self.debug_mode:
            print("\n🧠 [ANALYST THOUGHTS - INPUT PROMPT]")
            print("-" * 40)
            print(prompt)
            print("-" * 40)

        # 3. Invoke LLM (Retry Loop)
        for attempt in range(2):
            response = self.llm.invoke(prompt)
            code_text = response.content
            
            # 4. DEBUG: Print Raw Output
            if self.debug_mode:
                print(f"\n🤖 [ANALYST GENERATED CODE - ATTEMPT {attempt+1}]")
                print("-" * 40)
                print(code_text)
                print("-" * 40)

            # 5. Execute Code
            # execute_python_code handles the cleaning of ```python tags
            output_log, _ = execute_python_code(code_text, df)

            # 6. Validate Output
            if "Error" not in output_log and len(output_log.strip()) > 10:
                print(f"   ✅ Code executed successfully.")
                if self.debug_mode:
                    print(f"   📄 Output Log:\n{output_log[:500]}...\n")
                return output_log, code_text
            
            else:
                print(f"   ⚠️ Code Attempt {attempt+1} Failed/Empty. Reason: {output_log[:100]}...")
                # Optional: You could modify the prompt here to include the error message for the next attempt

        return "Analysis Failed: Code execution returned errors.", ""