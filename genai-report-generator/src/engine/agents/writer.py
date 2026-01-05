import yaml
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage
from src.engine.llm import get_llm

# Load prompt configuration
PROMPT_PATH = Path(__file__).parent.parent / "prompts/writer.yaml"
with open(PROMPT_PATH, "r") as f:
    prompt_config = yaml.safe_load(f)

def writer_agent(context_text: str, analysis_result: str):
    """
    Synthesizes text content and data analysis into a final report.
    args:
        context_text: Raw text extracted from the PDF (for qualitative context)
        analysis_result: The calculated number/string from the Analyst Agent
    """
    print("--- ✍️  Writer Agent: Drafting Report ---")
    
    # 1. Prepare the Input Context
    # We combine the qualitative text with the quantitative hard facts
    user_content = f"""
    DOCUMENT CONTEXT:
    {context_text[:3000]}... (truncated to fit context window)
    
    ANALYST FINDINGS:
    {analysis_result}
    """
    
    # 2. Initialize LLM (Reasoning Mode)
    llm = get_llm(model_type="reasoning")
    
    # 3. Construct Messages
    messages = [
        SystemMessage(content=prompt_config['instruction']),
        HumanMessage(content=user_content)
    ]
    
    # 4. Generate Report
    response = llm.invoke(messages)
    
    print("--- ✅ Report Generated ---")
    return response.content