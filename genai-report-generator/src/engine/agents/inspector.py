import json
import re
import logging
import pandas as pd
from src.engine.llm import get_llm
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

class InspectorAgent:
    def __init__(self):
        self.llm = get_llm()

    def inspect_and_plan(self, df: pd.DataFrame) -> dict:
        """
        Analyzes a CLEANED DataFrame and generates a comprehensive execution plan.
        """
        print(f"--- 🕵️ Inspector Agent: Analyzing Schema ({len(df)} rows, {len(df.columns)} cols) ---")
        
        # 1. Identify Column Types for Context
        # We pre-calculate this to give the LLM a head start
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower() or 'year' in col.lower()]
        cat_cols = list(df.select_dtypes(include=['object', 'category']).columns)
        num_cols = list(df.select_dtypes(include=['number']).columns)

        # 2. Prepare Context for LLM
        schema_info = {
            "columns": list(df.columns),
            "primary_id": df.columns[0], # Usually the first column is the ID/Key
            "date_columns": date_cols,
            "categorical_columns": cat_cols,
            "numeric_columns": num_cols,
            "sample_data": df.head(3).to_dict(orient='records')
        }
        
        # 3. Comprehensive Prompt
        # Forces the LLM to look for Trends, Rankings, and Primary Key analysis.
        prompt = f"""
        You are a Senior Data Architect. Analyze this CLEANED dataset structure and generate a COMPREHENSIVE Analysis Plan.

        ### DATA CONTEXT
        - **Primary Key/ID:** '{schema_info['primary_id']}'
        - **Numeric Metrics:** {schema_info['numeric_columns']}
        - **Categorical Dimensions:** {schema_info['categorical_columns']}
        - **Time Dimensions:** {schema_info['date_columns']}
        - **Sample Data:** {json.dumps(schema_info['sample_data'], indent=2, default=str)}

        ### TASK
        Generate a JSON object containing a detailed analysis strategy.
        Do NOT limit yourself to 3 questions. Generate as many relevant questions as the data supports (up to 8).

        ### STRATEGY GUIDELINES:
        1. **Primary Entity Analysis:** Always start by analyzing the Primary Key (e.g., "Total Quantity by {schema_info['primary_id']}").
        2. **Dimensional Breakdowns:** For every major categorical column (Region, Shift, Station, Dept), ask for a breakdown of the key metrics.
        3. **Time Series (If Applicable):** If 'Time Dimensions' exist, MUST ask for "Trend of [Metric] over Time/Month/Year".
        4. **Distribution/Rankings:** Ask for "Top 5" and "Bottom 5" performers.
        5. **Financial Logic:** If dataset is FINANCIAL, identify Income vs Expense rows.

        ### OUTPUT FORMAT (Strict JSON)
        Return ONLY valid JSON. No markdown.
        {{
            "dataset_type": "TRANSACTIONAL" | "FINANCIAL_STATEMENT" | "INVENTORY",
            "primary_dimensions": ["list", "of", "cols"],
            "primary_metrics": ["list", "of", "cols"],
            "analysis_questions": [
                "1. Calculate Total [Metric] by {schema_info['primary_id']} (Primary Breakdown)",
                "2. Analyze [Metric] distribution across [Category Column]",
                "3. Trend of [Metric] over [Date Column]",
                "4. Identify Top 10 {schema_info['primary_id']} by [Metric]"
            ]
        }}
        """

        # 4. Invoke LLM
        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            content = response.content.strip()

            # 5. Parse JSON with Retry Logic
            # Extract JSON from potential markdown blocks ```json ... ```
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group(0))
                
                # Sanity Check: Ensure 'analysis_questions' is a list
                if not isinstance(plan.get('analysis_questions'), list):
                    # Try to fix it if it's a string
                    if isinstance(plan.get('analysis_questions'), str):
                        plan['analysis_questions'] = [plan['analysis_questions']]
                    else:
                        raise ValueError("LLM returned malformed questions list")

                print(f"   ✅ Plan Generated: {plan.get('dataset_type', 'Unknown')} with {len(plan['analysis_questions'])} distinct analyses.")
                return plan
            else:
                raise ValueError("No JSON block found")

        except Exception as e:
            logger.error(f"Inspector Parse Error: {e}. Falling back to default plan.")
            return self._get_fallback_plan(df)

    def _get_fallback_plan(self, df):
        """
        If LLM fails, generate a simple plan based on column types.
        """
        numerics = list(df.select_dtypes(include=['number']).columns)
        objects = list(df.select_dtypes(include=['object', 'string']).columns)
        
        return {
            "dataset_type": "GENERIC",
            "primary_dimensions": objects[:2], # Take first 2 text cols
            "primary_metrics": numerics[:2],   # Take first 2 number cols
            "analysis_questions": [
                f"Calculate Sum of {numerics[0]} by {objects[0]}" if numerics and objects else "Count rows"
            ]
        }