import json
import re
import pandas as pd
from src.engine.llm import get_llm

class InspectorAgent:
    def __init__(self):
        self.llm = get_llm()

    def inspect_and_plan(self, df: pd.DataFrame) -> dict:
        """
        Analyzes a CLEANED DataFrame and generates an execution plan.
        """
        print(f"--- 🕵️ Inspector Agent: Analyzing Schema ({len(df)} rows, {len(df.columns)} cols) ---")
        
        # 1. Prepare Context for LLM
        # We don't send the whole file. We send the structure.
        columns = list(df.columns)
        dtypes = df.dtypes.to_dict()
        
        # Convert dtypes to string representation for JSON serialization
        dtypes_str = {k: str(v) for k, v in dtypes.items()}
        
        # Get a markdown sample (first 3 rows) to show the LLM what the data looks like
        try:
            sample_data = df.head(3).to_markdown(index=False)
        except ImportError:
            sample_data = df.head(3).to_string(index=False)

        # 2. Generalized Prompt
        # This works for ANY file because it asks for abstract "Dimensions" and "Metrics"
        prompt = f"""
        You are a Senior Data Architect. Analyze this CLEANED dataset structure.

        ### DATA CONTEXT
        - **Columns:** {columns}
        - **Data Types:** {dtypes_str}
        - **Sample Data:**
        {sample_data}

        ### TASK
        You must create a plan for a Python Analyst to generate insights.
        
        1. **Classify Dataset:**
           - "TRANSACTIONAL" (Events, Sales, Logs -> Row-by-row data)
           - "FINANCIAL_STATEMENT" (P&L, Balance Sheet -> Pre-aggregated metrics)
           
        2. **Identify Variables:**
           - **Dimensions:** Categorical columns useful for grouping (e.g., Region, Product, Date, Metric Name).
           - **Metrics:** Numeric columns useful for math (e.g., Amount, Quantity, Count).

        3. **Generate 3 Analysis Questions:**
           - Create 3 specific questions that can be answered using GroupBy and Sum/Mean.
           - Example: "Calculate Total [Metric] by [Dimension]"

        4. **SEMANTIC CLASSIFICATION (Crucial):**
           - Identify which rows represent **INCOME/REVENUE** (Positive flow).
           - Identify which rows represent **EXPENSES/COSTS** (Negative flow).
           - Identify which rows are **AGGREGATES** (e.g., "Total", "EBITDA", "Profit") vs **RAW ITEMS**.
           
        5. **GENERATE CONSTRAINTS:**
           - If calculating 'Total Revenue', explicitly state: "Filter rows where Metric contains 'Revenue'. Do NOT sum the whole column."
           - If calculating 'Margins', explicitly state: "Use the row labeled 'EBITDA' or 'Margin'. Do not recalculate unless necessary."

        ### OUTPUT FORMAT (Strict JSON)
        Return ONLY valid JSON. No markdown.
        {{
            "dataset_type": "TRANSACTIONAL" or "FINANCIAL_STATEMENT",
            "primary_dimensions": ["col_name_1", "col_name_2"],
            "primary_metrics": ["col_name_3", "col_name_4"],
            "analysis_questions": [
                "Question 1",
                "Question 2",
                "Question 3"
            ]
        }}
        """

        # 3. Invoke LLM
        response = self.llm.invoke(prompt)
        content = response.content.strip()

        # 4. Parse JSON with Retry Logic
        try:
            # Extract JSON from potential markdown blocks ```json ... ```
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group(0))
                print(f"   ✅ Plan Generated: {plan['dataset_type']} with {len(plan['analysis_questions'])} questions.")
                return plan
            else:
                raise ValueError("No JSON block found")

        except Exception as e:
            print(f"   ⚠️ Inspection Parse Error: {e}. Falling back to default plan.")
            return self._get_fallback_plan(df)

    def _get_fallback_plan(self, df):
        """
        If LLM fails, generate a stupid simple plan based on column types.
        """
        numerics = list(df.select_dtypes(include=['number']).columns)
        objects = list(df.select_dtypes(include=['object', 'string']).columns)
        
        return {
            "dataset_type": "UNKNOWN",
            "primary_dimensions": objects[:2], # Take first 2 text cols
            "primary_metrics": numerics[:2],   # Take first 2 number cols
            "analysis_questions": [f"Calculate sum of {numerics[0]} by {objects[0]}"] if numerics and objects else []
        }