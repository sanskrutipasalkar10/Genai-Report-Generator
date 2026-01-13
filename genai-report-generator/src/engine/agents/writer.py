import yaml
import os
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage
from src.engine.llm import get_llm

# Define the directory where prompts are stored
PROMPT_PATH = Path(__file__).parent.parent / "prompts/writer.yaml"

def load_prompt_config():
    """Safe loader for YAML config with fallback."""
    if PROMPT_PATH.exists():
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

def writer_agent(context_data: str, report_type: str = "Strategic Report") -> str:
    """
    Synthesizes text content, data analysis, and charts into a final Markdown report.
    
    Args:
        context_data (str): The full string containing Summary, Details, and Visuals.
        report_type (str): The title/style of the report.
    """
    print(f"--- ✍️  Writer Agent: Drafting '{report_type}' ---")
    
    # 1. Load Configuration
    config = load_prompt_config()
    
    # 2. Define System Prompt (With Currency Guards)
    # We explicitly inject the currency rule here to override any LLM defaults
    base_instruction = config.get('instruction', f"""
    You are a Senior Business Analyst writing a {report_type}.
    Structure the report with clear headings, bullet points, and professional tone.
    """)

    currency_guard = """
    CRITICAL FORMATTING RULES:
    1. **NO CURRENCY ASSUMPTIONS**: Do NOT add '$', '€', '£', or 'USD' symbols to numbers unless they explicitly appear in the input text.
    2. **RESPECT SOURCE UNITS**: If the input says "Rs", "Cr", or "Lakhs", use those exact terms. If no unit is given, simply use the number (e.g., "48,023").
    3. **PRESERVE ACCURACY**: Do not round numbers heavily (e.g., keep 48,023, don't change to 48k unless asked).
    """

    system_prompt = f"{base_instruction}\n\n{currency_guard}"

    # 3. Construct the User Input
    # We pass the consolidated context from the pipeline
    user_content = f"""
    REPORT TITLE: {report_type}
    
    INPUT DATA & ANALYSIS:
    {context_data}
    
    TASK:
    Write a cohesive report in Markdown format. 
    - Start with a Title (#).
    - Include an Executive Summary.
    - Create a 'Key Insights' section.
    - Create a 'Recommendations' section.
    - Embed the image links provided in the 'Visual Evidence' section exactly as they are.
    """
    
    # 4. Initialize LLM
    # We remove 'model_type="reasoning"' to ensure compatibility with your get_llm() wrapper
    llm = get_llm() 
    
    # 5. Construct Messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    
    # 6. Generate Report
    try:
        response = llm.invoke(messages)
        content = response.content
        print("--- ✅ Report Generated ---")
        return content
    except Exception as e:
        print(f"❌ Writer Error: {e}")
        return f"# Error Generating Report\n\nSystem encountered an error: {e}\n\n## Raw Data\n{context_data}"